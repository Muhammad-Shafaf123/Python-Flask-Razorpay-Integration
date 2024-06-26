from flask import jsonify, request
from flask.views import MethodView

from . import v1
from model.subscription import Subscription, Plan, User
from extension import db, client


class Subscriptions(MethodView):
    def get(self):
        subscription = Subscription.query.all()
        sub_obj = [
            {
                "id" : sub.id,
                "plan_id" : sub.plan_id,
                "razorpay_user_id" : sub.razorpay_user_id,
                "subscription_id" : sub.subscription_id,
                "user_id": sub.user_id,
                "subscription_status" : sub.subscription_status
            }
                for sub in subscription
            ]
        return jsonify(sub_obj), 200
    
    def post(self):
        req: dict = request.get_json()
        plan_id = req.get("plan_id")
        
        if plan_id is None:
            return jsonify({"message": "plan_id is required"}), 400

        # check is valid plan id
        if not Plan.query.filter_by(id=plan_id).all():
            return jsonify({"message" : "Not a valid plan_id"})
            
        if not Plan.query.filter_by(id=plan_id).all():
            return jsonify({"message" : "Not a valid plan_id"})
        
        # get plan id.
        razorpay_plan_id = Plan.query.filter_by(id=plan_id).first()
        
        # check is valid user_id
        user_id = req.get("user_id")
        if user_id is not None:
            user_exists = User.query.filter_by(id=user_id).first()
            if not user_exists:
                return jsonify({"message": "Not a valid user_id"}), 400
       
        try:
            subscription = client.subscription.create({
                "plan_id": razorpay_plan_id.plan_id,
                "customer_notify": 1,
                "quantity": req.get("quantity"),
                "total_count": req.get("total_count"),
                "notes": req.get("notes")
            })
            
            sub = Subscription(
                plan_id = req.get("plan_id"),
                total_count = req.get("total_count"),
                notes = req.get("notes"),
                quantity = req.get("quantity"),
                razorpay_user_id = req.get("razorpay_user_id"),
                subscription_id = req.get("subscription_id"),
                user_id = user_id,
                subscription_status = req.get("subscription_status")
            )
            
            db.session.add(sub)
            db.session.commit()
            
            return jsonify({"id": sub.id, "payment_url" : subscription["short_url"]}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    
v1.add_url_rule("/subscription", view_func=Subscriptions.as_view("subscription"))
