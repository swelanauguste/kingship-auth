from django.conf import settings
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import ClientApp, UserRole
from .utils import create_one_time_token, verify_and_mark_token


def sso_login(request):
    """
    Render login form (or use Django's AuthenticationForm).
    Accepts ?client_id=...&next=...
    After successful login, create a one-time token and redirect to client with ?token=...
    """
    client_id = request.GET.get("client_id")
    next_url = request.GET.get("next")

    if not client_id or not next_url:
        return HttpResponseBadRequest("Missing client_id or next parameter")

    try:
        app = ClientApp.objects.get(client_id=client_id)
    except ClientApp.DoesNotExist:
        return HttpResponseBadRequest("Unknown client_id")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            django_login(request, user)
            token = create_one_time_token(user, app)
            # redirect to client callback with token
            redirect_to = f"{next_url}?token={token}"
            return redirect(redirect_to)
        else:
            return render(
                request,
                "accounts/sso_login.html",
                {"error": "Invalid credentials", "next": next_url},
            )
    return render(request, "accounts/sso_login.html", {"next": next_url})


@csrf_exempt
def sso_verify(request):
    """
    POST { token: "..." } --> returns JSON { username, email, roles } on success or error.
    Client app exchanges one-time token for user info.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    # extract token from POST or JSON body
    token = request.POST.get("token")
    if not token:
        try:
            import json
            body = json.loads(request.body.decode())
            token = body.get("token")
        except Exception:
            token = None

    if not token:
        return JsonResponse({"error": "missing_token"}, status=400)

    user, app, err = verify_and_mark_token(token)
    if err:
        return JsonResponse({"error": err}, status=400)

    # get user roles for this app
    roles = list(
        UserRole.objects.filter(user=user, app=app).values_list("role__name", flat=True)
    )

    return JsonResponse(
        {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": roles,
            "app": app.name,
        }
    )
