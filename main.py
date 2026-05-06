from flask import Flask, render_template, url_for
from alertasAD import listar_alertas_quiebre

app = Flask(__name__)

@app.route("/")
def index():  # Este nombre es único para la raíz
    alertas_data = listar_alertas_quiebre()
    return render_template('alertas.html', 
                           alertas=alertas_data, 
                           total_q=len(alertas_data), 
                           total_r=3)

@app.route("/revendedores")
def revendedores():  # CAMBIA ESTE NOMBRE, antes seguro decía "index"
    alertas_data = listar_alertas_quiebre()
    return render_template('revendedores.html', 
                           total_q=len(alertas_data), 
                           total_r=3)

if __name__ == "__main__":
    app.run(debug=True)