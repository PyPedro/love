from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from models import db, Motivo, Configuracao
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///motivos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Inicializa o banco de dados
db.init_app(app)

# Cria as tabelas se não existirem
def init_db():
    with app.app_context():
        # Remove todas as tabelas existentes
        db.drop_all()
        # Cria todas as tabelas novamente
        db.create_all()
        # Cria a configuração inicial
        config = Configuracao(qtd_motivos=10)
        db.session.add(config)
        db.session.commit()

# Garante que a pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_config():
    config = Configuracao.query.first()
    if not config:
        config = Configuracao(qtd_motivos=10)
        db.session.add(config)
        db.session.commit()
    return config

@app.route("/qrcode")
def gerar_qrcode():
    # Gera o link absoluto para a página de motivos
    motivos_url = url_for('meus_motivos', _external=True)
    
    # Gera o QR code usando qrcode
    import qrcode
    from io import BytesIO
    
    # Cria o QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(motivos_url)
    qr.make(fit=True)

    # Cria a imagem do QR code com cores personalizadas
    img = qr.make_image(fill_color="#ff4b6e", back_color="white")
    
    # Salva a imagem em um buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')

@app.route("/", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        texto = request.form.get("motivo")
        imagem = request.files.get("imagem")
        if texto:
            qtd_motivos = Motivo.query.count()
            if qtd_motivos < 10:
                motivo = Motivo(texto=texto)
                
                if imagem and imagem.filename:
                    # Salva a imagem se foi enviada
                    ext = os.path.splitext(imagem.filename)[1]
                    filename = f"motivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                    imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    motivo.imagem_url = f"uploads/{filename}"
                
                db.session.add(motivo)
                db.session.commit()
                flash("Motivo cadastrado com sucesso! ❤️")
            else:
                flash("Você já cadastrou todos os 10 motivos! 💝")
        return redirect(url_for("cadastrar"))
    
    config = get_config()
    motivos = Motivo.query.order_by(Motivo.data_criacao.desc()).all()
    return render_template("cadastrar.html", motivos=motivos, config=config)

@app.route("/meus-motivos")
def meus_motivos():
    motivos = Motivo.query.order_by(Motivo.data_criacao.desc()).all()
    return render_template("meus_motivos.html", motivos=motivos)

@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_motivo(id):
    motivo = Motivo.query.get_or_404(id)
    
    # Remove a imagem se existir
    if motivo.imagem_url:
        try:
            os.remove(os.path.join(app.static_folder, motivo.imagem_url))
        except:
            pass
    
    db.session.delete(motivo)
    db.session.commit()
    flash("Motivo removido com sucesso!")
    return redirect(url_for("cadastrar"))

# Adiciona headers de segurança globalmente
@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com 'unsafe-inline'"
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/ver-imagem/<int:id>", methods=["GET", "POST"])
def ver_imagem(id):
    motivo = Motivo.query.get_or_404(id)
    
    # Lista de mensagens para momentos já vistos
    mensagens = [
        "Alguns momentos são únicos e especiais como este amor... ❤️",
        "Como pétalas de rosa, cada momento é único e irrepetível... 🌹",
        "O amor é feito de momentos únicos, como este que já passou... 💝",
        "Assim como um pôr do sol, cada momento de amor é único... 🌅",
        "Como uma estrela cadente, este momento já brilhou... ⭐",
    ]

    # Para requisições POST (quando a imagem é aberta em tela cheia)
    if request.method == "POST":
        # Se já foi visualizada, retorna erro
        if motivo.imagem_visualizada:
            return jsonify({
                "error": "já visualizada",
                "mensagem": mensagens[id % len(mensagens)]
            }), 400
            
        # Se tem imagem e ainda não foi visualizada, marca como vista
        if motivo.imagem_url and not motivo.imagem_visualizada:
            motivo.imagem_visualizada = True
            motivo.visualizado = True
            motivo.data_visualizacao = datetime.utcnow()
            db.session.commit()
            return jsonify({"success": True})
            
        return jsonify({"success": False}), 400
    
    # Para requisições GET (carregamento inicial da página)
    if motivo.imagem_visualizada:
        flash(mensagens[id % len(mensagens)], "info")
        return redirect(url_for("meus_motivos"))
    
    # Se não tem imagem, marca como visualizado imediatamente
    if not motivo.imagem_url and not motivo.visualizado:
        motivo.visualizado = True
        motivo.data_visualizacao = datetime.utcnow()
        db.session.commit()
    
    return render_template("ver_imagem.html", motivo=motivo)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
