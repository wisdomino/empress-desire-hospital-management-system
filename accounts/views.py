from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class RoleBasedLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        # ✅ Patients always go to portal after login
        if getattr(user, "role", None) == "patient":
            return reverse_lazy("patients:patient_portal")

        # ✅ Staff go to patient list (or respect ?next= handled by LoginView)
        return self.get_redirect_url() or reverse_lazy("patients:patient_list")

