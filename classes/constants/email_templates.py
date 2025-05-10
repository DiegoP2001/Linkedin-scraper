CONNECTIONS_ACCEPTED_BY_FERNANDO = """
    <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Fernando ha aceptado nuevas solicitudes de contacto</title>
                <style>
                    body {
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    h1 {
                        color: #0077B5;
                    }
                    .contact {
                        display: flex;
                        align-items: center;
                        margin-bottom: 20px;
                        border-bottom: 1px solid #eee;
                        padding-bottom: 20px;
                    }
                    .contact img {
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        margin-right: 20px;
                    }
                    .contact-info {
                        flex-grow: 1;
                    }
                    .contact-name {
                        font-size: 18px;
                        font-weight: bold;
                        color: #0077B5;
                        text-decoration: none;
                    }
                </style>
            </head>
            <body style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;">
                <h1>Fernando ha aceptado nuevas solicitudes de contacto</h1>
                <p>Aquí estan las personas que han solicitado nuestro contacto:</p>
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%; border-collapse: collapse;">
                    [Contacts]
                </table>
                <p>Sería interesante echarle un vistazo a alguno.</p>
            </body>
            </html>
"""

OTP_EMAIL = """
        <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your OTP Code</title>
        <style>
            body {
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                background-color: #f9f9f9;
                border-radius: 5px;
                padding: 20px;
                text-align: center;
            }
            .logo {
                max-width: 150px;
                margin-bottom: 20px;
            }
            .otp-code {
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 5px;
                margin: 20px 0;
                color: #007bff;
            }
            .footer {
                margin-top: 20px;
                font-size: 12px;
                color: #666666;
            }
        </style>
    </head>
    <body style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;">
        <div class="container">
            <img src="https://ekiona.com/contenido/media/2018/03/logo-ekiona.png" alt="Logo EKIONA" class="logo">
            <h1>Código de verificación</h1>
            <p>Este código debes ingresarlo para cambiar la contraseña:</p>
            <div class="otp-code" id="otpCode">[Token]</div>
            <p>Este código expirará en 10 minutos.</p>
            <p>Si no has pedido este código, por favor ignora este email</p>
            <div class="footer">
                <p>Este es un mensaje automático, por favor no respondas a él.</p>
                <p>&copy; 2025 EKIONA Iluminación Solar. Todos .</p>
            </div>
        </div>
        <script>
        function copyOTP() {
            var otpText = document.getElementById('otpCode').innerText;
            navigator.clipboard.writeText(otpText).then(function() {
                //alert('OTP copied to clipboard!');
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        }
    </script>
    </body>
    </html>
"""

AFTER_CONTACT_NO_RESPONSE_EMAIL = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contacto a través de Fernando – Farolas solares para tus proyectos</title>
    <style>
        body {
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #f4f4f4;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
        }
        .footer {
            background-color: #f4f4f4;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }
    </style>
</head>
<body style="font-family: 'Trebuchet MS', 'Lucida Sans Unicode', 'Lucida Grande', 'Lucida Sans', Arial, sans-serif;"> 
    <div class="header">
        <h1>Farolas solares para tus proyectos</h1>
    </div>
    <div class="content">
        <p>Hola [Nombre],</p>

        <p>Soy [Tu Nombre] de EKIONA Iluminación Solar. Mi compañero Fernando me ha pasado tu contacto, y quería presentarte nuestra solución en farolas solares, ideales para proyectos que requieran iluminación eficiente, sostenible y sin costos de conexión a la red eléctrica.</p>

        <p>Trabajamos con empresas y administraciones que buscan reducir consumo energético y costos de instalación en espacios como:</p>
        <ul>
            <li>Vías públicas</li>
            <li>Urbanizaciones</li>
            <li>Parques</li>
            <li>Proyectos industriales o logísticos</li>
            <li>Carreteras y viales</li>
        </ul>

        <p>Me gustaría saber si estás gestionando algún proyecto donde este tipo de iluminación pueda encajar. ¿Te parece si coordinamos una breve llamada para comentarlo?</p>

        <p>Quedo atento a tu respuesta.  Gracias por tu tiempo.</p>

        <p>Saludos,<br>
        [Tu Nombre]</p>
    </div>
    <div class="footer">
        <p>EKIONA Iluminación Solar<br>
        +34 693364337<br>
        marcel.buzainz@ekiona.com</p>
    </div>
</body>
</html>
"""