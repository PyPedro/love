from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Motivo(db.Model):
    __tablename__ = 'motivos'
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    imagem_url = db.Column(db.String(200))
    imagem_visualizada = db.Column(db.Boolean, default=False)
    visualizado = db.Column(db.Boolean, default=False)
    data_visualizacao = db.Column(db.DateTime, nullable=True)

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    id = db.Column(db.Integer, primary_key=True)
    qtd_motivos = db.Column(db.Integer, nullable=False, default=10)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
