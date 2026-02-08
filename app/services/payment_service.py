import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY

class PaymentService:
    def create_payment_intent(self, amount: int, currency: str = "usd", metadata: dict = None) -> stripe.PaymentIntent:
        """
        Create a Stripe PaymentIntent.
        Amount is in cents.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            return intent
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe Error: {str(e)}")

    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Verify and construct webhook event.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError("Invalid signature")

payment_service = PaymentService()
