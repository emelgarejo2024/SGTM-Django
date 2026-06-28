import pytest
from datetime import date, time, timedelta
from turnos.models import Especialidad, BloqueDisponibilidad, Reserva
from turnos.factories import UsuarioFactory
from turnos.services import ReservaFacade


@pytest.mark.django_db
class TestReservaFacade:

    @pytest.fixture
    def setup_datos(self):
        # Esta función "fixture" prepara los datos base para no repetir
        # código en cada test
        paciente = UsuarioFactory.crear_usuario(
            "PACIENTE", "11111111-1", "pac_test", "123", "Juan", "A", "j@cl.cl"
        )
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "22222222-2", "med_test", "123", "Dr", "B", "m@cl.cl"
        )
        especialidad = Especialidad.objects.create(nombre="Cardiología")

        # Creamos un bloque para mañana (asegurando que no sea
        # sábado ni domingo para no chocar con lógicas de negocio)
        manana = date.today() + timedelta(days=2)
        bloque = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=especialidad,
            fecha=manana,
            hora_inicio=time(10, 0),
            hora_fin=time(10, 30),
        )
        return paciente, medico, bloque

    def test_crear_reserva_exitosa(self, setup_datos):
        paciente, _, bloque = setup_datos

        # 1. Ejecutamos la fachada
        exito, mensaje = ReservaFacade.procesar_reserva_atomica(
            bloque_id=bloque.id, paciente=paciente
        )

        # 2. Verificamos que se creó correctamente
        assert exito is True
        assert "Reserva exitosa ID:" in mensaje
        assert Reserva.objects.count() == 1

        # El bloque debería cambiar su estado (esta_disponible = False)
        bloque.refresh_from_db()
        assert bloque.esta_disponible is False

        # La reserva debe quedar asignada
        reserva = Reserva.objects.first()
        assert reserva.bloque == bloque
        assert reserva.paciente == paciente

    def test_falla_por_overbooking(self, setup_datos):
        paciente1, _, bloque = setup_datos
        paciente2 = UsuarioFactory.crear_usuario(
            "PACIENTE", "33333333-3", "pac2", "123", "Pedro", "C", "p@cl.cl"
        )

        # 1. El primer paciente toma el bloque exitosamente
        exito1, mensaje1 = ReservaFacade.procesar_reserva_atomica(
            bloque_id=bloque.id, paciente=paciente1
        )
        assert exito1 is True

        # 2. El segundo paciente intenta tomar el mismo bloque exacto
        exito2, mensaje2 = ReservaFacade.procesar_reserva_atomica(
            bloque_id=bloque.id, paciente=paciente2
        )
        assert exito2 is False
        assert "El bloque ya fue tomado" in mensaje2

        # 3. Verificamos que la base de datos protegió la integridad
        # (solo debe haber 1 reserva)
        assert Reserva.objects.count() == 1

    def test_falla_por_bloque_inexistente(self, setup_datos):
        paciente, _, _ = setup_datos

        # Intentamos reservar un bloque con ID 999 que no existe
        exito, mensaje = ReservaFacade.procesar_reserva_atomica(
            bloque_id=999, paciente=paciente
        )
        assert exito is False
        assert "no existe" in mensaje

    def test_falla_por_limite_reservas_br17(self, setup_datos):
        """Verifica que un paciente no pueda superar el límite de 3 reservas activas."""
        paciente, medico, bloque_nuevo = setup_datos
        especialidad = Especialidad.objects.first()

        # 1. Simulamos que el paciente ya tiene 3 reservas activas
        for i in range(3):
            bloque_previo = BloqueDisponibilidad.objects.create(
                medico=medico,
                especialidad=especialidad,
                fecha=date.today() + timedelta(days=10 + i),
                hora_inicio=time(9, 0),
                hora_fin=time(9, 30),
                esta_disponible=False
            )
            Reserva.objects.create(
                paciente=paciente, 
                bloque=bloque_previo, 
                estado="RESERVADO"
            )

        # 2. Intentamos hacer la cuarta reserva usando el bloque de setup_datos
        exito, mensaje = ReservaFacade.procesar_reserva_atomica(
            bloque_id=bloque_nuevo.id, paciente=paciente
        )

        # 3. Verificamos que el sistema la rechace correctamente
        assert exito is False
        assert "límite máximo de 3 reservas activas" in mensaje
        # Verificamos que en la BD solo existan las 3 reservas originales
        assert Reserva.objects.filter(paciente=paciente).count() == 3


@pytest.mark.django_db
class TestReservaFacadeConsultas:
    """Cubre los métodos de consulta de ReservaFacade (líneas 53 y 59-66)."""

    @pytest.fixture
    def datos_consulta(self):
        medico = UsuarioFactory.crear_usuario(
            "MEDICO", "99999999-9", "dr_cons", "123", "Dra", "C", "drc@cl.cl"
        )
        esp1 = Especialidad.objects.create(nombre="Dermatología")
        esp2 = Especialidad.objects.create(nombre="Neurología")
        manana = date.today() + timedelta(days=2)
        pasado = date.today() + timedelta(days=5)

        bloque1 = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp1,
            fecha=manana,
            hora_inicio=time(9, 0),
            hora_fin=time(9, 30),
        )
        bloque2 = BloqueDisponibilidad.objects.create(
            medico=medico,
            especialidad=esp2,
            fecha=pasado,
            hora_inicio=time(11, 0),
            hora_fin=time(11, 30),
        )
        return esp1, esp2, bloque1, bloque2, manana, pasado

    def test_obtener_especialidades(self, datos_consulta):
        """Cubre ReservaFacade.obtener_especialidades() — línea 53."""
        esp1, esp2, *_ = datos_consulta
        especialidades = ReservaFacade.obtener_especialidades()
        nombres = list(especialidades.values_list("nombre", flat=True))
        assert "Dermatología" in nombres
        assert "Neurología" in nombres

    def test_obtener_bloques_disponibles_sin_filtros(self, datos_consulta):
        """Cubre sin filtros de obtener_bloques_disponibles."""
        *_, bloque1, bloque2, manana, pasado = datos_consulta
        bloques = ReservaFacade.obtener_bloques_disponibles()
        ids = [b.id for b in bloques]
        assert bloque1.id in ids
        assert bloque2.id in ids

    def test_obtener_bloques_disponibles_filtrado_por_especialidad(
        self, datos_consulta
    ):
        """Cubre rama de filtro por especialidad — líneas 61-62."""
        esp1, esp2, bloque1, bloque2, *_ = datos_consulta
        bloques = ReservaFacade.obtener_bloques_disponibles(
            especialidad_id=esp1.id
        )
        ids = [b.id for b in bloques]
        assert bloque1.id in ids
        assert bloque2.id not in ids

    def test_obtener_bloques_disponibles_filtrado_por_fecha(
        self, datos_consulta
    ):
        """Cubre rama de filtro por fecha — líneas 63-64."""
        *_, bloque1, bloque2, manana, pasado = datos_consulta
        bloques = ReservaFacade.obtener_bloques_disponibles(fecha=manana)
        ids = [b.id for b in bloques]
        assert bloque1.id in ids
        assert bloque2.id not in ids

    def test_obtener_bloques_no_incluye_ocupados(self, datos_consulta):
        """Verifica que bloques con esta_disponible=False no aparecen."""
        *_, bloque1, bloque2, manana, pasado = datos_consulta
        bloque1.esta_disponible = False
        bloque1.save()
        bloques = ReservaFacade.obtener_bloques_disponibles()
        ids = [b.id for b in bloques]
        assert bloque1.id not in ids
        assert bloque2.id in ids
