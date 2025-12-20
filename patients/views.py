from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PatientForm
from .models import Patient

User = get_user_model()


def _is_patient_user(user) -> bool:
    return getattr(user, "role", None) == "patient"


@login_required
def patient_create(request):
    # ✅ Patients cannot access staff registration page
    if _is_patient_user(request.user):
        return redirect("patients:patient_portal")

    form = PatientForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        patient = form.save(commit=False)

        # ✅ Password-reset only: auto-create patient user (no default password)
        if patient.email:
            user, created = User.objects.get_or_create(
                username=patient.email,
                defaults={
                    "email": patient.email,
                    "role": "patient",
                },
            )

            # Ensure patient users cannot login until they set password via reset
            if created:
                user.set_unusable_password()
                user.save()

            # Link patient to user (whether newly created or existing)
            patient.user = user

            # Trigger password reset email/link (prints to console if EMAIL_BACKEND is console)
            reset_form = PasswordResetForm({"email": patient.email})
            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    use_https=request.is_secure(),
                    from_email=None,  # set when SMTP is configured
                    email_template_name="registration/password_reset_email.html",
                    subject_template_name="registration/password_reset_subject.txt",
                )

        patient.save()
        return redirect("patients:patient_detail", patient.id)

    return render(request, "patients/patient_form.html", {"form": form})


@login_required
def patient_list(request):
    # ✅ Patients cannot access staff patient list
    if _is_patient_user(request.user):
        return redirect("patients:patient_portal")

    q = (request.GET.get("q") or "").strip()
    qs = Patient.objects.all().order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(hospital_number__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
        )

    return render(request, "patients/patient_list.html", {"patients": qs[:200], "q": q})


@login_required
def patient_detail(request, pk: int):
    # ✅ If logged-in user is a patient, only allow their own record
    if _is_patient_user(request.user):
        my_patient = getattr(request.user, "patient", None)
        if not my_patient:
            raise PermissionDenied("Patient profile not linked.")
        if my_patient.pk != pk:
            raise PermissionDenied("You cannot view another patient's record.")
        return render(request, "patients/patient_detail.html", {"patient": my_patient})

    # Staff access
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, "patients/patient_detail.html", {"patient": patient})


@login_required
def patient_portal(request):
    patient = getattr(request.user, "patient", None)
    if patient is None:
        return redirect("patients:patient_list")  # staff fallback

    visits = patient.visits.all().order_by("-created_at")
    return render(
        request,
        "patients/patient_portal.html",
        {
            "patient": patient,
            "visits": visits,
        },
    )
