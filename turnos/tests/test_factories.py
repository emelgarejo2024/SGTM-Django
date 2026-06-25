import pytest
from turnos.factories import UsuarioFactory
from django.contrib.auth import get_user_model

Usuario = get_user_model()

@pytest.mark.django_db
class TestUsuarioFactory:
    
    def test_crear_paciente_exitoso(self):
        # 1. Preparación (Arrange) & Ejecución (Act)
        paciente = UsuarioFactory.crear_usuario(
            tipo_rol='PACIENTE',
            rut='33333333-3',
            username='paciente_test',
            password='securepassword123',
            first_name='Juan',
            last_name='Pérez',
            email='juan@correo.cl'
        )
        
        # 2. Verificación (Assert)
        assert paciente.username == 'paciente_test'
        assert paciente.email == 'juan@correo.cl'
        # Verificamos que la contraseña se haya encriptado correctamente (no se guarda en texto plano)
        assert paciente.check_password('securepassword123') is True
        # Verificamos que se haya guardado en la base de datos temporal
        assert Usuario.objects.count() == 1

    def test_crear_medico_exitoso(self):
        # 1. Preparación & Ejecución
        medico = UsuarioFactory.crear_usuario(
            tipo_rol='MEDICO',
            rut='11111111-1',
            username='dr_test',
            password='admin123',
            first_name='Gregory',
            last_name='House',
            email='house@sgtm.cl'
        )
        
        # 2. Verificación
        assert medico.username == 'dr_test'
        assert medico.check_password('admin123') is True
        assert Usuario.objects.count() == 1

    def test_falla_con_rol_invalido(self):
        # Verificamos que la Factory proteja el sistema levantando un error
        # si alguien intenta crear un rol que no existe
        with pytest.raises(ValueError):
            UsuarioFactory.crear_usuario(
                tipo_rol='HACKER',
                rut='99999999-9',
                username='bad_user',
                password='123',
                first_name='Bad',
                last_name='User',
                email='bad@correo.cl'
            )