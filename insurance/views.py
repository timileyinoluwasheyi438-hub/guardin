import uuid
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import UserProfile, Policy, Claim
from .forms import ProfileUpdateForm, ClaimForm, PolicyForm
from django.contrib.auth.models import User


def home(request):
    return render(request, 'insurance/home.html')



def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        # Validate
        if not all([first_name, last_name, username, email, password1, password2]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'insurance/signup.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'insurance/signup.html')

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'insurance/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
            return render(request, 'insurance/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with that email already exists.')
            return render(request, 'insurance/signup.html')

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        messages.success(request, f'Welcome, {first_name}! Your account is ready.')
        return redirect('dashboard')

    return render(request, 'insurance/signup.html')



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'insurance/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='/login/')
def dashboard(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    policies = Policy.objects.filter(user=user)
    claims   = Claim.objects.filter(user=user)

    active_policies = policies.filter(status='active')
    open_claims     = claims.exclude(status__in=['paid', 'rejected'])
    total_paid      = claims.filter(status='paid').aggregate(
                          total=Sum('claim_amount'))['total'] or 0

    context = {
        'user':                 user,
        'profile':              profile,
        'policies':             policies,
        'claims':               claims,
        'active_policies':      active_policies,
        'open_claims':          open_claims,
        'total_paid':           total_paid,
        'active_policy_count':  active_policies.count(),
        'open_claim_count':     open_claims.count(),
'total_premium_paid':   policies.aggregate(
                                    total=Sum('premium_amount'))['total'] or 0,
        'recent_claims':        claims.order_by('-created_at')[:3],
    }
    return render(request, 'insurance/dashboard.html', context)


@login_required(login_url='/login/')
def file_claim(request):
    if request.method == 'POST':
        form = ClaimForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.user = request.user
            claim.claim_number = 'CLM-' + str(uuid.uuid4())[:8].upper()
            claim.save()
            messages.success(request, 'Claim submitted successfully!')
            return redirect('dashboard')
    else:
        form = ClaimForm(request.user)

    return render(request, 'insurance/file_claim.html', {'form': form})


@login_required(login_url='/login/')
def add_policy(request):
    if request.method == 'POST':
        form = PolicyForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.user = request.user
            policy.policy_number = 'POL-' + str(uuid.uuid4())[:8].upper()
            policy.save()
            messages.success(request, 'Policy added successfully!')
            return redirect('dashboard')
    else:
        form = PolicyForm()

    return render(request, 'insurance/add_policy.html', {'form': form})


@login_required(login_url='/login/')
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=profile,
            user=request.user
        )
        if form.is_valid():
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            # Show form errors
            print(form.errors)
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)

    return render(request, 'insurance/profile.html', {
        'form': form, 
        'profile': profile
    })