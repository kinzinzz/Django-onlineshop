from django.shortcuts import render, get_object_or_404
from .models import *
from cart.cart import Cart
from .forms import *

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            if cart.coupon:
                order.coupon = cart.coupon
                # 할인 쿠폰 로직1
                # order.discount = cart.coupon.amount
                
                # 할인 쿠폰 로직2
                order.discount = cart.get_discount_total()
                order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'] )
            cart.clear()
            return render(request, 'order/created.html', {'order':order,})
    else:
        # 주문자 정보를 입력받는 페이지
        form = OrderCreateForm()
    return render(request, 'order/create.html', {'cart':cart, 'form':form})

# JS 동작하지 않는 환경에서도 주문은 가능해야한다.
def order_complete(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order/created.html', {'order':order})

from django.views.generic.base import View
from django.http import JsonResponse

# class view
class OrderCreateAjaxView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
                return JsonResponse({"authenticated":False}, status=403)
        cart = Cart(request)
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.coupon:
                order.coupon = cart.coupon
                # 할인 쿠폰 로직1
                # order.discount = cart.coupon.amount
                
                # 할인 쿠폰 로직2
                order.discount = cart.get_discount_total()
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'] )
            cart.clear()
            
            # 데이터 응답
            data = {
                'order_id':order.id
            }
            return JsonResponse(data)
        
        else:
            return JsonResponse({}, status=401)
        
class OrderCheckoutAjaxView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
                return JsonResponse({"authenticated":False}, status=403)       

        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)
        amount = request.POST.get('amount')
        
        try:
           merchant_order_id = OrderTransaction.objects.create_new(
               order = order,
               amount=amount
           )
        except:
            merchant_order_id = None
            
        if merchant_order_id is not None:
            data = {
                'works':True,
                "merchant_id":merchant_order_id,
            } 
            return JsonResponse(data)
        
        else:
            return JsonResponse({}, status=401)
# 결제 확인        
class OrderImAjaxView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
                return JsonResponse({"authenticated":False}, status=403)  
            
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id) 
        
        merchant_id = request.POST.get('merchant_id')
        imp_id = request.POST.get('imp_id')
        amount = request.POST.get('amount')
        
        try:
            trans = OrderTransaction.objects.get(
                order=order,
                merchant_id=merchant_id,
                amount=amount
            )    
        except:
            trans = None
            
        if trans is not None:
            trans.transaction_id = imp_id
            # trans.success = True
            trans.save()
            order.paid = True
            order.save()
            
            data = {
                'works':True,
            }
            return JsonResponse(data)
        else:
            return JsonResponse({}, status=401)