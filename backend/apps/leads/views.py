from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import DemoRequest
from .serializers import DemoRequestSerializer


class DemoRequestCreateView(CreateAPIView):
    """Public endpoint behind the landing page's "Bepul demo so'rash" form.

    Open to anyone (no auth, no organization) and rate-limited by IP so the
    form can't be used to spam. On success it stores the lead and answers with
    a short confirmation the page shows to the visitor.
    """

    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "demo_request"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "detail": "So'rovingiz qabul qilindi. Tez orada siz bilan bog'lanamiz.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
