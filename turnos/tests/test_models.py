import pytest
from datetime import date, time, timedelta
from django.core.exceptions import ValidationError
from turnos.models import Especialidad, BloqueDisponibilidad, Reserva
from turnos.factories import UsuarioFactory
from django.urls import reverse


@pytest.mark.django_db
class TestModelos:

    # ------------------------------------------------------------------ #
    #  Especialidad                                                        #
    # ------------------------------------------------------------------ #
    def test_especialidad_str(self):
        """Cubre el método __str__ de Especialidad (línea 27 models.py)."""
        esp = Especialidad.objects.create(nombre="Traumatología")
        assert str(esp) == "Traumatología"

    # ------------------------------------------------------------------ #
    #  Usuario                                                             #
    # ------------------------------------------------------------------ #
    def test_usuario_str(self):
        """Cubre __str__ de Usuario (línea 16 models.py)."""
        usuario = UsuarioFactory.crear_usuario(
            "PACIENTE",
            "12345678-9",
            "juan_str",
            "123",
            "Juan",
            "Pérez",
            "jp@cl.cl",
        )
        # get_full_name() devuelve "Juan Pérez"
        assert str(usuario) == "Juan Pérez - 12345678-9"

    # ------------------------------------------------------------------ #
    #  BloqueDisponibilidad — validaciones de clean()                     #
    # ------------------------------------------------------------------ #
    def test_bloque_hora_inicio_mayor_a_fin_falla(self):
        """Hora inicio >= hora fin debe lanzar ValidationError (línea 60)."""
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "88888888-8", "dr_test_mod", "123", "M", "A", "m@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Pediatría")
        manana = date.today() + timedelta(days=1)

        bloque_invalido = BloqueDisponibilidad(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(11, 0),
            hora_fin=time(10, 0),  # ¡Inválido!
        )

        with pytest.raises(ValidationError):
            bloque_invalido.clean()

    def test_bloque_superposicion_falla(self):
        """Dos bloques superpuestos deben lanzar ValidationError."""
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "77777777-7", "dr_sup", "123", "Dr", "Sup", "sup@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Cardiología")
        manana = date.today() + timedelta(days=3)

        # Bloque existente: 09:00 – 10:00
        BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
        )

        # Bloque nuevo que se superpone: 09:30 – 10:30
        bloque_superpuesto = BloqueDisponibilidad(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(9, 30),
            hora_fin=time(10, 30),
        )

        with pytest.raises(ValidationError):
            bloque_superpuesto.clean()

    def test_bloque_str(self):
        """Cubre __str__ de BloqueDisponibilidad (línea 81)."""
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "66666666-6", "dr_blk", "123", "Ana", "B", "ana@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Neurología")
        manana = date.today() + timedelta(days=4)

        bloque = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(8, 0),
            hora_fin=time(8, 30),
        )

        resultado = str(bloque)
        # El __str__ incluye el nombre del médico y "Libre" por defecto
        assert "Ana" in resultado
        assert "Libre" in resultado

    # ------------------------------------------------------------------ #
    #  Reserva                                                             #
    # ------------------------------------------------------------------ #
    def test_reserva_str(self):
        """Cubre __str__ de Reserva (línea 102)."""
        paciente = UsuarioFactory.crear_usuario(
            "PACIENTE",
            "55555555-5",
            "pac_str",
            "123",
            "Carlos",
            "R",
            "cr@cl.cl",
        )
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "44444444-4", "dr_res_str", "123", "Dr", "Z", "drz@cl.cl"
        )
        esp = Especialidad.objects.create(nombre="Oftalmología")
        manana = date.today() + timedelta(days=5)

        bloque = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp,
            fecha=manana,
            hora_inicio=time(14, 0),
            hora_fin=time(14, 30),
        )
        reserva = Reserva.objects.create(
            paciente=paciente, bloque=bloque, estado="RESERVADO"
        )

        resultado = str(reserva)
        assert "Carlos" in resultado
        assert "RESERVADO" in resultado

    def test_api_especialidades_vacia(self, client):
        response = client.get(reverse("api_especialidades"))
        assert response.status_code == 200
        assert response.json()["especialidades"] == []
