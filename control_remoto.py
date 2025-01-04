from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

# Ruta para servir el archivo HTML con el botón
@app.get("/", response_class=HTMLResponse)
def read_index():
    with open("templates_remo/indexcontrol.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Ruta para alternar el estado de las luces
@app.post("/toggle_lights")
def toggle_lights():
    try:
        # Envía una solicitud HTTP a la computadora 2 que ejecuta Tkinter
        response = requests.post("http://192.168.43.107:5000/update_lights")
        return {"message": response.json()["message"]}
    except requests.exceptions.RequestException as e:
        return {"error": "No se pudo conectar con la Computadora 2"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
