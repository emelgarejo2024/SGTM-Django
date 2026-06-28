from django import forms
from .models import Usuario

class RegistroPacienteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        # Aquí ponemos los campos básicos que pide tu BD para crear el usuario
        fields = ['username', 'rut', 'email', 'first_name', 'last_name']
        labels = {
            'username': 'Nombre de Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido'
        }

    def save(self, commit=True):
        # Guarda el usuario base aplicando el hashing a la contraseña
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user