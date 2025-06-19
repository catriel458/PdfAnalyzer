@echo off
echo ===============================================
echo   CREACION DE EJECUTABLE ANALIZADOR DE PDFs
echo ===============================================
echo.
echo Este script creara un ejecutable portable del
echo Analizador de PDFs que podra distribuirse
echo facilmente sin necesidad de instalar Python.
echo.
echo Asegurese de tener el archivo "analizador_pdfs.py"
echo en la misma carpeta que este script.
echo.
echo Presione cualquier tecla para continuar...
pause > nul

python build_exe.py

echo.
echo Proceso finalizado. Revise la carpeta generada.
echo Presione cualquier tecla para salir.
pause > nul