from typing import List, Dict, Set, Any, Tuple
from sqlalchemy.orm import Session
import models

class GraphService:
    """
    Servicio de Graph Engineering para la CMDB y el Catálogo de Servicios de TI:
    1. Detección y prevención de ciclos en jerarquías y dependencias técnicas.
    2. Recorrido de dependencias (upstream traversal) para análisis de impacto.
    3. Identificación de servicios de TI afectados por la indisponibilidad de CIs.
    """

    @staticmethod
    def check_hierarchy_cycle(db: Session, categoria_id: int, prospective_parent_id: int) -> bool:
        """
        Verifica si asignar prospective_parent_id a categoria_id crearía un ciclo en la jerarquía.
        Retorna True si hay ciclo (inválido), False si es seguro.
        """
        if categoria_id == prospective_parent_id:
            return True
        
        current_id = prospective_parent_id
        visited: Set[int] = {categoria_id}

        while current_id is not None:
            if current_id in visited:
                return True
            visited.add(current_id)
            parent = db.query(models.CategoriaCI).filter(models.CategoriaCI.id == current_id).first()
            if not parent or parent.parent_id is None:
                break
            current_id = parent.parent_id

        return False

    @staticmethod
    def check_ci_relationship_cycle(db: Session, origen_id: int, destino_id: int, tipo_relacion: str) -> bool:
        """
        Para relaciones técnicas dirigidas ('depende_de', 'alojado_en'), la estructura
        debe ser estrictamente un Grafo Dirigido Acíclico (DAG).
        Si agregar la arista origen -> destino crea un ciclo (es decir, ya existe un camino destino -> origen),
        retorna True (ciclo detectado).
        Para 'conectado_a', se permite topología mallada o cíclica (redes/switches).
        """
        if tipo_relacion == "conectado_a":
            # La topología de conexión de red admite ciclos (ej. anillos, mallas redundantes)
            return False

        if origen_id == destino_id:
            return True

        # Buscamos si existe un camino dirigido desde destino_id hacia origen_id usando BFS
        visited: Set[int] = set()
        queue: List[int] = [destino_id]

        while queue:
            curr = queue.pop(0)
            if curr == origen_id:
                return True # ¡Ciclo detectado!
            if curr in visited:
                continue
            visited.add(curr)

            # Relaciones salientes dirigidas del mismo tipo o dependencia equivalente
            salientes = db.query(models.CIRelationship).filter(
                models.CIRelationship.ci_origen_id == curr,
                models.CIRelationship.tipo_relacion.in_(["depende_de", "alojado_en"]),
                models.CIRelationship.activo == True
            ).all()

            for rel in salientes:
                if rel.ci_destino_id not in visited:
                    queue.append(rel.ci_destino_id)

        return False

    @staticmethod
    def analyze_impact(db: Session, ci_id: int) -> Dict[str, Any]:
        """
        Realiza un recorrido de dependencias en el grafo de la CMDB partiendo del CI indicado:
        - Identifica todos los CIs que dependen directa o indirectamente de este componente.
        - Identifica todos los Servicios de TI de Nivel 2 (y sus Nivel 1) potencialmente afectados.
        - Emite advertencia explícita sobre interrupción vs. dependencia.
        """
        ci_root = db.query(models.ConfigurationItem).filter(models.ConfigurationItem.id == ci_id).first()
        if not ci_root:
            return {"error": "Elemento de configuración no encontrado", "ci_id": ci_id}

        # Conjunto de CIs afectados (iniciando por el raíz)
        affected_ci_ids: Set[int] = {ci_id}
        traversal_queue: List[int] = [ci_id]
        edges: List[Dict[str, Any]] = []

        # Buscamos quién depende de este CI:
        # Si B depende_de A, y A falla -> B se ve afectado.
        # Por tanto, buscamos aristas donde ci_destino_id == curr (o ci_origen_id aloja a ci_destino_id)
        while traversal_queue:
            curr_id = traversal_queue.pop(0)

            # CIs que dependen de curr_id: rel.ci_destino_id == curr_id and rel.tipo == 'depende_de'
            # (El origen depende del destino)
            dependents = db.query(models.CIRelationship).filter(
                models.CIRelationship.ci_destino_id == curr_id,
                models.CIRelationship.tipo_relacion.in_(["depende_de", "alojado_en"]),
                models.CIRelationship.activo == True
            ).all()

            for rel in dependents:
                edges.append({
                    "origen_id": rel.ci_origen_id,
                    "destino_id": rel.ci_destino_id,
                    "tipo": rel.tipo_relacion
                })
                if rel.ci_origen_id not in affected_ci_ids:
                    affected_ci_ids.add(rel.ci_origen_id)
                    traversal_queue.append(rel.ci_origen_id)

        # Consultar datos completos de los CIs afectados
        cis_afectados = db.query(models.ConfigurationItem).filter(
            models.ConfigurationItem.id.in_(affected_ci_ids)
        ).all()

        ci_list = []
        for c in cis_afectados:
            ci_list.append({
                "id": c.id,
                "codigo": c.codigo,
                "nombre": c.nombre,
                "tipo_ci": c.tipo_ci,
                "estado_actual": c.estado_actual,
                "ubicacion_fisica": c.ubicacion_fisica,
                "es_raiz": (c.id == ci_id)
            })

        # Buscar todos los servicios de Nivel 2 vinculados directamente a cualquiera de los CIs afectados
        servicios_links = db.query(models.CIServicio).filter(
            models.CIServicio.ci_id.in_(affected_ci_ids)
        ).all()

        servicios_afectados_dict = {}
        for link in servicios_links:
            s2 = link.servicio
            if s2 and s2.id not in servicios_afectados_dict:
                s1_nombre = s2.servicio_nivel1.nombre if s2.servicio_nivel1 else "Sin N1"
                s1_codigo = s2.servicio_nivel1.codigo if s2.servicio_nivel1 else "N/A"
                servicios_afectados_dict[s2.id] = {
                    "id": s2.id,
                    "codigo": s2.codigo,
                    "nombre": s2.nombre,
                    "nivel1_codigo": s1_codigo,
                    "nivel1_nombre": s1_nombre,
                    "criticidad_relacion": link.criticidad_relacion,
                    "vinculado_a_ci_id": link.ci_id
                }

        return {
            "ci_raiz": {
                "id": ci_root.id,
                "codigo": ci_root.codigo,
                "nombre": ci_root.nombre,
                "tipo_ci": ci_root.tipo_ci,
                "estado_actual": ci_root.estado_actual
            },
            "total_cis_en_arbol_impacto": len(ci_list),
            "cis_impactados": ci_list,
            "aristas_dependencia": edges,
            "total_servicios_afectados": len(servicios_afectados_dict),
            "servicios_potencialmente_afectados": list(servicios_afectados_dict.values()),
            "advertencia_tecnica": (
                "Decisión de Arquitectura: La existencia de una relación de dependencia "
                "identifica un riesgo potencial sobre los servicios de TI vinculados. "
                "No implica necesariamente una interrupción efectiva inmediata si existen "
                "mecanismos de redundancia, alta disponibilidad (HA) o tolerancia a fallos."
            )
        }
