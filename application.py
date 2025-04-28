from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from dashboardrvTools import RVToolsAnalyzer

app = FastAPI()

# Archivos estáticos (reportes generados)
app.mount("/output", StaticFiles(directory="output"), name="output")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def copiar_reporte_a_output(origen):
    """
    Copia el reporte HTML y las imágenes necesarias a la carpeta /output.
    Retorna el nombre del HTML público.
    """
    carpeta_origen = os.path.dirname(origen)
    nombre_carpeta = os.path.basename(carpeta_origen)
    carpeta_destino = os.path.join("output", nombre_carpeta)
    os.makedirs(carpeta_destino, exist_ok=True)

    # Copiar el HTML
    shutil.copyfile(origen, os.path.join(carpeta_destino, "reporte.html"))

    # Copiar todas las imágenes PNG generadas
    for file in os.listdir(carpeta_origen):
        if file.endswith(".png"):
            shutil.copyfile(
                os.path.join(carpeta_origen, file),
                os.path.join(carpeta_destino, file)
            )

    # Retornar ruta relativa pública
    return f"{nombre_carpeta}/reporte.html"



@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    path = f"./temp/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analyzer = RVToolsAnalyzer(path)
    analyzer.generate_report()

    reporte_generado = os.path.join(analyzer.output_dir, "reporte.html")
    reporte_publico = copiar_reporte_a_output(reporte_generado)

    return templates.TemplateResponse("success.html", {"request": request, "report": reporte_publico})


@app.post("/ruta")
async def usar_ruta(request: Request, ruta: str = Form(...)):
    if not os.path.exists(ruta):
        return HTMLResponse(f"<h2>El archivo no existe: {ruta}</h2>", status_code=404)

    analyzer = RVToolsAnalyzer(ruta)
    analyzer.generate_report()

    reporte_generado = os.path.join(analyzer.output_dir, "reporte.html")
    reporte_publico = copiar_reporte_a_output(reporte_generado)

    return templates.TemplateResponse("success.html", {"request": request, "report": reporte_publico})

application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("application:app", host="0.0.0.0", port=8000, reload=True)