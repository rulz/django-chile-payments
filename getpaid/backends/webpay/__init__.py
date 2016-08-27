import os
import glob
import datetime
import urllib
from collections import OrderedDict
from itertools import starmap
from shutil import copyfile, rmtree
from stat import S_IEXEC
from subprocess import Popen, PIPE
from tempfile import mkdtemp, mkstemp
from contextlib import contextmanager
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from getpaid.backends import PaymentProcessorBase


TBK_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAxKKjroxE7X44TQovh9A9
ZpntP7LrdoyFsnJbDKjOOCoiid92FydN5qemyQCeXhsc7QHUXwGdth22fB8xJr3a
MZBEUJ+BKFrL+W6yE5V+F5Bj0Uq3lL0QMAIftGhLpgqw0ZMtU89kyd9Q4Rclq4r8
p2m/ZD7Pn5EmTOFSeyoWTMZQDl7OEoCKh/cZH5NJdWL08lCI+sGLOghRmFzkve4h
F9JCwKA7NYG7j3BWh39Oj2NIXEY/TO1Y3Y2WfNv9nvTpr46SpFlyp0KOhSiqgvXX
DgeXlebyqS82ch2DzOV9fjDAw7t71WXJBAev8Gd6HXwIXE/JP6AnLCa2Y+b6Wv8K
GWBCMIBXWL0m7WHeCaJ9Hx2yXZmHJh8FgeKffFKCwn3X90JiMocOSGsOE+Sfo85S
h/39Vc7vZS3i7kJDDoz9ab9/vFy30RuJf4p8Erh7kWtERVoG6/EhR+j4N3mgIOBZ
SHfzDAoOnqP5l7t2RXYcEbRLVN6o+XgUtalX33EJxJRsXoz9a6PxYlesIwPbKteD
BZ/xyJDwTc2gU2YzSH8G9anKrcvITBDULSAuxQUkYOiLbkb7vSKWDYKe0do6ibO3
RY/KXI63Q7bGKYaI2aa/8GnqVJ2G1U2s59NpqX0aaWjn59gsA8trA0YKOZP4xJIh
CvLM94G4V7lxe2IHKPqLscMCAwEAAQ==
-----END PUBLIC KEY-----
"""

PRIVADA_PEM = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAn3HzPC1ZBzCO3edUCf/XJiwj3bzJpjjTi/zBO9O+DDzZCaMp
14aspxQryvJhv8644E19Q+NHfxtz1cxd2wnSYKvay1gJx30ZlTOAkzUj4QMimR16
vomLlQ3T2MAz1znt/PVPVU7T/JOG9R+EbiHNVKa/hUjwJEFVXLQNME97nHoLjb3v
V5yV2aVhmox7b54n6F3UVPHvCsHKbJpXpE+vnLpVmdETbNpFVrDygXyG+mnEvyiO
BLIwEY3XTMrgXvS069groLi5Gg8C5LDaYOWjE9084T4fiWGrHhn2781R1rykunTu
77wiWPuQHMS0+YC7mhnsk8Z/ilD+aWz/vhsgHwIDAQABAoIBAQCM+Nrt4cpNKQmn
+Ne8348CGRS9ACXp6WRg6OCQXO4zM7lRZAminVgZgSQXE6aJR+T9rIWMeG7GWydX
aJGzEEQJZOjV0MkUr+7mk9qiTOGkGHmGlyHnRQU8jDU59vXe3UEl3l5+NmwHbQht
waf9F7XLmoLK/WoVJA6tICRpCl1oQrpziqN+gjdmMpz9i8I1sMFE7+Y7xf+7S2u7
c1MRPUWqgdS9yViQVh3vZi25m5CyKRVnOB0hpNuZ7nrJymtADYSWt9wV2W1fX+MX
UUoYfxyQQvWryHhGdedU7GGAnoEdblUcDkBuAaFmsm1P8K4HQZLWP4v6pYlW2JLa
Zoaerb3BAoGBANCRevl0CLB0HBU7sCs0eN9fTkIEsh3OVIxPSBqDnKsynJrIWovK
cs37Vb6phzdQO3ADoFJvR9ck8+v6Cv0KR8IOFl9wfC4ZoxkKBBeq94ZLN+YhE2PW
KiRFybqcgCtzxKS3MyWgpIcT9xFtHVjlorZ8Jk51fgLZbGzamtLhderVAoGBAMO0
mIiiV4l2vXzu4tFfkpu/GOx/D9/vAic3X9FOky09BNCyuMXMQgI8e3wWsGEZghls
Vg9KDV5EPxAmpumcdPFK2IMACaH41ac7vys3ZD8kMK0INQkuDAcG4YsxMaTwEPo0
p1i3zwwEWwknw1yJkOyozz0EcIzS9NrZZEjnBHEjAoGAQ81XdeqzvHEyg/CQd6sq
NCtubGXMZYYi1C4d2Yi5kKn2YRcK4HDi23V+TWodK+0oNWToZIQKjbVUmn0Bv3rt
EvezbDlMFUx+SfCIng0VRJIFTQmpnQYNUxdg2gpwXC/ZWFa6CNxtQABMjFy1cqXM
PJild1IYseJurgBu3mkvBTUCgYBqA/T1X2woLUis2wPIBAv5juXDh3lkB6eU8uxX
CEe2I+3t2EM781B2wajrKadWkmjluMhN9AGV5UZ8S1P0DStUYwUywdx1/8RNmZIP
qSwHAGXV9jI0zNr7G4Em0/leriWkRM26w6fHjLx8EyxDfsohSbkqBrOptcWqoEUx
MOQ5HQKBgAS4sbddOas2MapuhKU2surEb3Kz3RCIpta4bXgTQMt9wawcZSSpvnfT
zs5sehYvBFszL3MV98Uc50HXMf7gykRCmPRmB9S+f+kiVRvQDHfc9nRNg2XgcotU
KAE16PQM8GihQ0C+EcXHouyud5CRJGfyurokRlH/jY3BiRAG5c+6
-----END RSA PRIVATE KEY-----
"""

TBK_PARAM_TXT = """
<BP_PAGO>
        <TR_NORMAL>
                TBK_TIPO_TRANSACCION#A#50#1
                TBK_MONTO#M#10#1
                TBK_ORDEN_COMPRA#A#26#1
                TBK_ID_SESION#A#61#0
                TBK_URL_FRACASO#A#256#1
                TBK_URL_EXITO#A#256#1
                TBK_MONTO_CUOTA#M#9#0
                TBK_NUMERO_CUOTAS#N#2#0
        </TR_NORMAL>
        <TR_COMPLETA>
                TBK_TIPO_TRANSACCION#A#50#1
                TBK_MONTO#M#10#1
                TBK_ORDEN_COMPRA#A#26#1
                TBK_ID_SESION#A#61#0
                TBK_URL_EXITO#A#256#1
                TBK_URL_FRACASO#A#256#1
                TBK_NUMERO_TARJETA#N#19#1
                TBK_FECHA_EXPIRACION#N#4#1
                TBK_CVV#N#4#1
                TBK_TIPO_PAGO#A#2#1
                TBK_NUMERO_CUOTAS#N#2#0
                TBK_MONTO_CUOTA#M#9#0
        </TR_COMPLETA>
        <TR_MALL>
                TBK_TIPO_TRANSACCION#A#50#1
                TBK_MONTO#M#10#1
                TBK_ORDEN_COMPRA#A#26#1
                TBK_ID_SESION#A#61#1
                TBK_URL_RESULTADO#A#256#1
                TBK_URL_FRACASO#A#256#1
                TBK_NUM_TRX#N#4#1
        </TR_MALL>
        <TR_MALL_COMPLETA>
                TBK_TIPO_TRANSACCION#A#50#1
                TBK_MONTO#M#10#1
                TBK_ORDEN_COMPRA#A#26#1
                TBK_ID_SESION#A#61#1
                TBK_URL_RESULTADO#A#256#1
                TBK_URL_FRACASO#A#256#1
                TBK_NUM_TRX#N#4#1
                TBK_NUMERO_TARJETA#N#19#1
                TBK_FECHA_EXPIRACION#N#4#1
                TBK_CVV#N#4#1
        </TR_MALL_COMPLETA>
        <TR_TASA_INTERES_MAX>
                TBK_TIPO_TRANSACCION#A#50#1
                TBK_URL_EXITO#A#256#1
                TBK_URL_FRACASO#A#256#1
        </TR_TASA_INTERES_MAX>
</BP_PAGO>
<BP_PAGO_MALL>
        <TR_MALL>
                TBK_CODIGO_TIENDA_M#N#12#1
                TBK_ORDEN_TIENDA_M#A#26#1
                TBK_MONTO_TIENDA_M#M#10#1
                TBK_MONTO_CUOTA_M#M#9#0
                TBK_NUMERO_CUOTAS_M#N#2#0
        </TR_MALL>
        <TR_MALL_COMPLETA>
                TBK_CODIGO_TIENDA_M#N#12#1
                TBK_ORDEN_TIENDA_M#A#26#1
                TBK_MONTO_TIENDA_M#M#10#1
                TBK_TIPO_PAGO_M#A#2#1
                TBK_NUMERO_CUOTAS_M#N#2#0
                TBK_MONTO_CUOTA_M#M#9#0
        </TR_MALL_COMPLETA>
</BP_PAGO_MALL>
"""

TBK_TRACE_DAT = """
GLEVEL     = 7

// niveles soportados  LOGINFO  1
//                     LOGERROR 2
//                     LOGFATAL 4
//
//                glebel 0 >>> No genera LOG
//
// combinatorias  glebel 1 >>> LOGINFO
//                glebel 2 >>> LOGERROR
//                glebel 3 >>> LOGINFO  + LOGERROR
//                glebel 4 >>> LOGFATAL
//                glebel 5 >>> LOGINFO  + LOGFATAL
//                glebel 6 >>> LOGERROR + LOGFATAL
//                glebel 7 >>> LOGINFO  + LOGERROR + LOGFATAL
"""


class PaymentProcessor(PaymentProcessorBase):
    BACKEND = 'getpaid.backends.webpay'
    BACKEND_NAME = _('Webpay backend')
    BACKEND_ACCEPTED_CURRENCY = ('CLP', 'USD')
    TESTING_COMMERCE_IDS = {'CLP': '597020000501',
                            'USD': '597026007984'}
    TBK_PARAM_TXT = TBK_PARAM_TXT
    TBK_TRACE_DAT = TBK_TRACE_DAT
    TBK_PUBLIC_KEY = TBK_PUBLIC_KEY
    PRIVADA_PEM = PRIVADA_PEM

    @classmethod
    def get_tbk_config(cls, payment_pk, currency='CLP'):
        domain = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        conf = OrderedDict((('IDCOMERCIO', None),
                            ('MEDCOM', '1'),
                            ('TBK_KEY_ID', '101'),
                            ('PARAMVERIFCOM', '1'),
                            ('URLCGICOM', "%s%s" % (domain, reverse('getpaid-webpay-resultado', args=[payment_pk]))),
                            ('SERVERCOM', cls.get_backend_setting('STATIC_INBOUND_IP')),
                            ('PORTCOM', '80'),
                            ('WHITELISTCOM', 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789./:=&?_'),
                            ('HOST', cls.get_backend_setting('STATIC_INBOUND_IP')),
                            ('WPORT', '80'),
                            ('URLCGITRA', '/filtroUnificado/bp_revision.cgi'),
                            ('URLCGIMEDTRA', '/filtroUnificado/bp_validacion.cgi'),
                            ('SERVERTRA', 'https://certificacion.webpay.cl'),
                            ('PORTTRA', '6443'),
                            ('PREFIJO_CONF_TR', 'HTML_'),
                            ('HTML_TR_NORMAL', "%s%s" % (domain, reverse('getpaid-webpay-close')))))

        certified = cls.get_backend_setting('CERTIFIED', False)
        if certified:
            conf.update({'IDCOMERCIO': cls.get_backend_setting('COMMERCE_ID_{}'.format(currency)),
                         'URLCGITRA': '/cgi-bin/bp_revision.cgi',
                         'URLCGIMEDTRA': '/cgi-bin/bp_validacion.cgi',
                         'SERVERTRA': 'https://webpay.transbank.cl',
                         'PORTTRA': '443'})
        else:
            conf['IDCOMERCIO'] = cls.TESTING_COMMERCE_IDS[currency]

        return "\n".join(starmap("{} = {}".format, conf.items()))

    @classmethod
    def get_tbk_param(cls):
        return cls.TBK_PARAM_TXT

    @classmethod
    def get_tbk_trace(cls):
        return cls.TBK_TRACE_DAT

    @classmethod
    def get_keys(cls):
        if cls.get_backend_setting('CERTIFIED', False):
            tbk_public_key = "\n" + cls.get_backend_setting('TRANSBANK_PUBLIC_KEY') + "\n"
            commerce_private_key = "\n" + cls.get_backend_setting('COMMERCE_PRIVATE_KEY') + "\n"
            return (tbk_public_key, commerce_private_key)
        else:
            return (cls.TBK_PUBLIC_KEY, cls.PRIVADA_PEM)

    @classmethod
    def validate(cls, payment, request):
        """Validates a Webpay transaction.

        Checks that:
            - The payment amount has not been tampered with.
            - The MAC is authentic (with help of tbk_check_mac.cgi).
            - The payment has yet to be paid.

        Args:
            payment: A getpaid.models.Payment instance.
            request: A django.http.HttpRequest instance.

        Returns:
            A bool.
        """

        # ESTAS TRES LINEAS VERIFICAN QUE EL MONTO REGISTRADO AL INICIAR EL
        # PROCESO DE COMPRA EN LA ORDEN (OBJETO 'payment') ES IGUAL AL RECIBIDO
        # DESPUES DE PASAR POR TRANSBANK (EN EL PARAMETRO 'TBK_MONTO')
        amount = str(int(payment.amount)) + '00'
        tbk_amount = request.POST.get('TBK_MONTO', None)
        same_amount = amount == tbk_amount

        temp_fd, temp_file = mkstemp()

        with open(temp_file, 'w') as params_file:
            params_file.write(urllib.unquote(request.body))

        # EN ESTE 'WITH' SE HACE EL CHECK_MAC
        with webpay_run('tbk_check_mac.cgi', payment.pk, temp_file) as cgi:
            output, _ = cgi.communicate()
            os.close(temp_fd)
            os.unlink(temp_file)
            valid_mac = output == 'CORRECTO\n'

        return same_amount and valid_mac and not payment.paid_on

    def get_gateway_url(self, request):
        """Returns the url the user will be redirected to.

        Webpay requires that the request to ``pago`` url must be via POST.
        ``tbk_params`` is returned as context to populate a hidden form that
        auto-submits to ``pago`` url.
        """
        order = self.payment.order
        base_url = settings.SITE_URL

        tbk_params = {'TBK_MONTO': str(order.total) + '00',
                      'TBK_TIPO_TRANSACCION': 'TR_NORMAL',
                      'TBK_ORDEN_COMPRA': order.pk,
                      'TBK_ID_SESION': self.payment.pk,
                      'TBK_URL_EXITO': base_url + reverse('getpaid-webpay-success'),
                      'TBK_URL_FRACASO': base_url + reverse('getpaid-webpay-failure')}

        return reverse('getpaid-webpay-pago', kwargs={'pk': self.payment.pk}), "POST", tbk_params


@contextmanager
def webpay_run(name, payment_pk, *args, **kwargs):
    """Runs a Webpay binary within a preconfigured environment.

    Before running the binary, this context manager recreates the
    directories and files in /tmp that the binary needs to run correctly,
    as if it were sitting in an standalone web server.

    Yields a subprocess.Popen instance with an open pipe to stdin and stdout.

    After running the binary, log and journal entries are captured and
    then temporary files are removed.

    Args:
        name: A string, basename of the binary as is found in assets_dir.
        payment_pk: An integer, primary key for the related payment. This
            is needed to associate the logs with their payment.
        *args: Extra positional arguments are appended to the command line
            before execution.

    Example:
        >>> webpay_run('tbk_bp_resultado.cgi', 3958) as cgi:
                output, _ = cgi.communicate("TBK_MONTO=384800&...\n")
                do_something_with(output)

    WARNING: Always use Popen with communicate() method when using PIPE
        or there will be deadlocks.
    """

    from pprint import pprint

    # prepare the configuration files
    assets_dir = PaymentProcessor.get_backend_setting('ASSETS_DIR')
    tbk_config = PaymentProcessor.get_tbk_config(payment_pk, 'CLP')  # FIXME
    tbk_param = PaymentProcessor.get_tbk_param()
    tbk_trace = PaymentProcessor.get_tbk_trace()

    temp_dir = mkdtemp()
    cgi_path = os.path.join(assets_dir, name)
    temp_cgi_path = os.path.join(temp_dir, name)
    datos_path = os.path.join(temp_dir, 'datos')

    os.mkdir(datos_path)
    with open(os.path.join(datos_path, 'tbk_config.dat'), 'w') as f:
        pprint("TBK_CONFIG: %s" % tbk_config)
        pprint('------------------------------------------')
        f.write(tbk_config)
    with open(os.path.join(datos_path, 'tbk_param.txt'), 'w') as f:
        f.write(tbk_param)
    with open(os.path.join(datos_path, 'tbk_trace.dat'), 'w') as f:
        f.write(tbk_trace)

    # prepare the public and private keys
    maestros_path = os.path.join(temp_dir, 'maestros')
    public_key, private_key = PaymentProcessor.get_keys()

    os.mkdir(maestros_path)
    with open(os.path.join(maestros_path, 'tbk_public_key.pem'), 'w') as f:
        f.write(public_key)
    with open(os.path.join(maestros_path, 'privada.pem'), 'w') as f:
        f.write(private_key)

    # prepare the log directory
    log_path = os.path.join(temp_dir, 'log')
    os.mkdir(log_path)

    # copy the binary to the temp dir and make it executable
    copyfile(cgi_path, temp_cgi_path)
    os.chmod(temp_cgi_path, S_IEXEC)

    yield Popen([temp_cgi_path] + list(args), stdin=PIPE, stdout=PIPE)

    # capture the logs
    try:
        from getpaid.models import Payment

        payment = Payment.objects.get(pk=payment_pk)

        for event_log in glob.glob(os.path.join(log_path, 'TBK_EVN*')):
            with open(event_log, 'r') as f:
                for line in map(str.strip, f.readlines()):
                    pprint("TBK_ENV: %s" % line)
                    from models import LogEntry

                    entry = LogEntry.from_line(line=line, payment=payment)
                    entry.save()
                pprint('------------------------------------------')

        for journal_log in glob.glob(os.path.join(log_path, 'tbk_bitacora_TR_NORMAL*')):
            st = os.stat(journal_log)
            date = datetime.date.fromtimestamp(st.st_mtime)
            with open(journal_log, 'r') as f:
                for line in map(str.strip, f.readlines()):
                    pprint("TBK_BITACORA: %s" % line)
                    from models import JournalEntry
                    entry = JournalEntry(date=date, body=line, payment=payment)
                    entry.save()
                pprint('------------------------------------------')
    except Payment.DoesNotExist:
        pass

    # clean up
    rmtree(temp_dir)
