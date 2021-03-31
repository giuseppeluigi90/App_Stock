from flask import Flask, render_template, redirect, url_for, request, flash, session, logging
from datetime import datetime, time
from flask_mysqldb import MySQL
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Establezco la llave secreta
app.secret_key = "appStockLogin"

# Configuro la conexion a MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD']  = 'admin'
app.config['MYSQL_DB'] = 'bd_appstock'

# Creo el objeto MySQL
mysql = MySQL(app)

""" class RegisterForm(Form):
    nombre = StringField('nombre', [validators.Length(min=1, max=50)])
    email = StringField('email', [validators.Length(min=4, max=255)])
    password = PasswordField('password', [
            validators.DataRequired(),
            validators.EqualTol('confirm', message='Password do not mach')
            ])
    confirm = PasswordField('Confirm Password') """

# context processors
@app.context_processor
def date_now():
    return {
        'now' : datetime.utcnow()
    }


# Ruta Princiap para login con validacion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Recoger datos de formulario
        usuario = request.form['usuario']
        password_canditato = request.form['contraseña']

        # Creamos el cursor a la BD
        cursor = mysql.connection.cursor()

        # Recogemos usuario por el usuario ingresado
        resulta = cursor.execute("SELECT * FROM user WHERE usuario =%s", [usuario])

        if resulta > 0:
            # Recogemos el registro y el campo password
            data = cursor.fetchone()
            password = data[2]

            # Comparamos los password
            if password == password_canditato:
                # Acceder
                session['logged_in'] = True
                session['usuario'] = usuario
                flash('Usuario validado, satisfactoriamente.') 
                app.logger.info('PASSWORD MATCHED')
                return render_template('panel.html')
            else:
                app.logger.info('Password no valida')
                error = 'Dato invalidado'
                flash('Contraseña incorrecta.') 
                return render_template('login.html', error=error)
            
                # Cerramos la conexion
                cursor.close()
        else:
            app.logger.info('NO ES UN USUARIO')
            error = 'Usuario no existe'
            flash('Usuario o contraseña invalida.') 
            return render_template('login.html', error=error)

    return render_template('login.html')

# Verificar si existe una sesion
def is_logged_in(f):
    @wraps(f)
    def wrap (*args, **kargs):
        if 'logged_in' in session:
            return f(*args, **kargs)
        else:
            flash('No autorizado, por favor inicie sesión.', 'Advertencia')
            return render_template('login.html')
    return wrap

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('panel.html')

# No tiene sesion
@app.route('/logout')
def logout():
    session.clear()
    flash('Usted no tiene sesion iniciada')
    return redirect(url_for('login'))

@app.route('/nuevo_producto', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':

        codigoproducto = request.form['codigo']
        nombre = request.form['nombreproducto']
        preciocompra = request.form['preciocompra']
        precioventa = request.form['precioventa']
        entradas = request.form['entradas']
        salidas = request.form['salidas']
        stockactual = request.form['stockactual']

        estado = ""

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO productos VALUES (%s, %s, %s, %s, %s, %s, %s)", (codigoproducto,nombre, preciocompra, precioventa, entradas, salidas, stockactual))
        cursor.execute("INSERT INTO inventario VALUES(%s, %s, %s, %s, %s, %s, %s)", (codigoproducto, codigoproducto, nombre, entradas, salidas, stockactual, estado))
        cursor.connection.commit()
        flash('Se ha registrado un nuevo producto. Gracias.')
    
        return render_template('nuevo_producto.html')

    return render_template('nuevo_producto.html')

# Ruta para Ver todos los productos
@app.route('/ver_productos')
def ver_productos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    return render_template('productos.html', productos=productos)

@app.route('/ver_movimientos')
def ver_movimientos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM movimientos")
    movimientos = cursor.fetchall()
    cursor.close()
    return render_template('movimientos.html', movimientos = movimientos)

@app.route('/ver_inventario')
def ver_inventario():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM inventario")
    inventarios = cursor.fetchall()
    cursor.close()
    return render_template('inventario.html', inventarios = inventarios)

@app.route('/nuevo_movimiento', methods=['GET', 'POST'])
def nuevo_movimiento():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    cursor.close()
    
    if request.method == 'POST':

        codigomovimiento = request.form['codigomovimiento']
        fecha = request.form['fecha']
        codigoproducto = request.form['codigoproducto']
        producto = request.form['producto']
        movimiento = request.form['movimiento']
        cantidad = request.form['cantidad']
        preciocompra = request.form['preciocompra']
        precioventa = request.form['precioventa']
        totalcompra = request.form['totalcompra']
        totalventa = request.form['totalventa']
        observacion = request.form['observacion']

        cursor = mysql.connection.cursor()
        productox = cursor.execute(f"SELECT * FROM inventario WHERE codigo_producto = {codigoproducto}" )
        

        if productox > 0:
            data = cursor.fetchone()
            entrada = data[3]
            salida = data[4]
            if int(movimiento) == 1:
                totalentrada = entrada + int(cantidad)
                totalsalida = salida + 0
            else:
                totalsalida = salida + int(cantidad)
                totalentrada = entrada + 0
        
        totalstock = totalentrada - totalsalida
            
        cursor.execute("INSERT INTO movimientos VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (codigomovimiento, fecha, codigoproducto, producto, movimiento, cantidad, preciocompra, precioventa, totalcompra, totalventa, observacion))
        cursor.execute(f"UPDATE inventario SET entradas = {totalentrada}, salidas = {totalsalida}, stock = {totalstock} WHERE codigo_producto = {codigoproducto}")
        cursor.execute(f"UPDATE productos SET stock = {totalstock} WHERE codigo = {codigoproducto}")
        cursor.connection.commit()
        flash('Se ha registrado el movimiento. Gracias.')
        
        return render_template('nuevo_movimiento.html')

    return render_template('nuevo_movimiento.html', productos = productos)

@app.route('/borrar-producto/<producto_codigo>')
def borrarProducto(producto_codigo):
    cursor = mysql.connection.cursor()
    cursor.execute(f"DELETE FROM productos WHERE codigo = {producto_codigo}")
    cursor.execute(f"DELETE FROM inventario WHERE codigo_producto = {producto_codigo}")
    cursor.execute(f"DELETE FROM movimientos WHERE codigo_producto = {producto_codigo}")
    mysql.connection.commit()
    flash('Producto eliminado correctamente')

    return redirect(url_for('ver_productos'))

@app.route('/borrar-movimiento')
def borrarMovimiento(movimiento_codigo, producto_codigo, movimiento):
  
    cursor = mysql.connection.cursor()
    cursor.execute(f"DELETE FROM movimientos WHERE codigo = {movimiento_codigo}")
    cursor.execute(f"UPDATE inventario SET entradas = {totalentrada}, salidas = {totalsalida}, stock = {totalstock} WHERE codigo_producto = {codigoproducto}")
    mysql.connection.commit()
    flash('Movimiento eliminado correctamente')

    return redirect(url_for('ver_movimientos'))

# Mantener la ejecucion en el servidor de flask abierta permanentemente
if __name__ == '__main__':
    app.run(debug=True)