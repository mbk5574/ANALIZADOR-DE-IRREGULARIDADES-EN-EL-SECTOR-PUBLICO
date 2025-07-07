from sqlalchemy import Column, String, DateTime, Enum, func
import enum, datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class JobStatus(str, enum.Enum):
    """
Estados posibles de un job de scraping.

Attributes:
    pending:   El job esta en cola, sin ejecutar.
    running:   El job esta en ejecución actualmente.
    finished:  El job ha finalizado correctamente.
    failed:    El job ha terminado pero con error.
    """
    pending  = "pending"
    running  = "running"
    finished = "finished"
    failed   = "failed"


class ScrapeJob(Base):
    """
Modelo que utilizaremos para gestionar una tarea de scraping en la base de datos.

Atributos de columna:
    __tablename__ (str): Nombre de la tabla en la BD ( en este caso: "jobs").

    id (str):
        Identificador unico UUID del job.  

    terms (str):
        JSON serializado con la lista de términos a buscar.  

    created_at (datetime):
        Timestamp de creación del registro.  
        Valor por defecto: NOW() en el servidor.

    updated_at (datetime):
        Timestamp de la última actualizacion del registro.  
        Se actualiza automáticamente en cada cambio.

    status (JobStatus):
        Estado actual del job.  
        Los valores posibles los hemos definido antes en la enumeracion JobStatus, por defecto es "pending".

    result_path (str):
        Ruta al fichero JSON donde se vuelcan los resultados.  
        Puede ser nulo hasta que el job acabe.
    """
    __tablename__ = "jobs"
    id          = Column(String, primary_key=True, index=True)
    terms       = Column(String, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False
    )
    status      = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    result_path = Column(String, nullable=True)
