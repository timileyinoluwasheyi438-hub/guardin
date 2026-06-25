from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import UserProfile, Policy, Claim
from .forms import ProfileUpdateForm, ClaimForm, PolicyForm
import uuid


def home(request):
    return render(request, 'insurance/home.html')

def about(request):
    return render(request, 'insurance/about.html')

def contact(request):
    return render(request, 'insurance/contact.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.POST.get('email', '')
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            # Auto-create profile
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to Guard.In, {user.first_name or user.username}!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'insurance/signup.html', {'form': form})


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
    # Auto-create profile if doesn't exist
    profile, _ = UserProfile.objects.get_or_create(user=user)

    policies = Policy.objects.filter(user=user)
    claims = Claim.objects.filter(user=user)

    active_policies = policies.filter(status='active')
    open_claims = claims.exclude(status__in=['paid', 'rejected'])
    total_paid = claims.filter(status='paid').aggregate(
        total=Sum('claim_amount'))['total'] or 0

    context = {
        'user': user,
        'profile': profile,
        'policies': policies,
        'claims': claims,
        'active_policies': active_policies,
        'open_claims': open_claims,
        'total_paid': total_paid,
        'active_policy_count': active_policies.count(),
        'open_claim_count': open_claims.count(),
        'total_premium_paid': policies.aggregate(
            total=Sum('premium_amount'))['total'] or 0,
        # Last 3 claims for recent activity
        'recent_claims': claims.order_by('-created_at')[:3],
    }
    return render(request, 'insurance/dashboard.html', context)


@login_required(login_url='/login/')
def file_claim(request):
    if request.method == 'POST':
        form = ClaimForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.user = request.user
            claim.claim_number = f"CLM-{uuid.uuid4().hex[:6].upper()}"
            claim.save()
            messages.success(request, f'Claim {claim.claim_number} filed successfully!')
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
            policy.policy_number = f"GI-{uuid.uuid4().hex[:8].upper()}"
            policy.save()
            messages.success(request, f'Policy {policy.policy_number} added!')
            return redirect('dashboard')
    else:
        form = PolicyForm()
    return render(request, 'insurance/add_policy.html', {'form': form})


@login_required(login_url='/login/')
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST, request.FILES,
            instance=profile, user=request.user
        )
        if form.is_valid():
            # Save user fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)
    return render(request, 'insurance/profile.html', {
        'form': form, 'profile': profile
    })
