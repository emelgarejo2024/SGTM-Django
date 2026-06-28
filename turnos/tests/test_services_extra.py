import pytest
from datetime import date, time, timedelta
from turnos.models import Especialidad, BloqueDisponibilidad
from turnos.services import reservar_bloque_seguro
from turnos.factories import UsuarioFactory


@pytest.mark.django_db
def test_reservar_bloque_ya_ocupado():
    paciente = UsuarioFactory.crear_usuario(
        "PACIENTE", "11111111-1", "p1", "123", "A", "B", "a@a.cl"
    )
    medico = UsuarioFactory.crear_usuario(
        "MEDICO", "22222222-2", "m1", "123", "Dr", "C", "c@c.cl"
    )
    esp = Especialidad.objects.create(nombre="Test")

    bloque = BloqueDisponibilidad.objects.create(
        medico=medico,
        especialidad=esp,
        fecha=date.today() + timedelta(days=1),
        hora_inicio=time(10, 0),
        hora_fin=time(10, 30),
        esta_disponible=False,  # 🔥 clave
    )

    exito, mensaje = reservar_bloque_seguro(bloque.id, paciente)

    assert not exito
    assert "ya fue tomado" in mensaje


@pytest.mark.django_db
def test_reservar_bloque_no_existe():
    paciente = UsuarioFactory.crear_usuario(
        "PACIENTE", "33333333-3", "p2", "123", "A", "B", "b@b.cl"
    )

    exito, mensaje = reservar_bloque_seguro(9999, paciente)

    assert not exito
    assert "no existe" in mensaje