from abc import ABC, abstractmethod
from datetime import date, datetime

class ICertificadoSostenible(ABC):
    @abstractmethod
    def obtener_certificado_verde(self): pass
    @abstractmethod
    def calcular_beneficio_tributario(self): pass

class HistorialMovimientos:
    def __init__(self): self._mov = []
    def registrar(self, tipo, monto, saldo):
        self._mov.append((datetime.now().strftime("%Y-%m-%d %H:%M"), tipo, monto, saldo))
    def __str__(self):
        return "\n".join(f"  [{f}] {t:10} ${m:>12,.2f}  Saldo: ${s:>12,.2f}" for f,t,m,s in self._mov) or "  (Sin movimientos)"

class Persona(ABC):
    def __init__(self, doc, nombre, email): self.doc, self.nombre, self.email = doc, nombre, email
    @abstractmethod
    def info(self): pass
    def __str__(self): return self.info()

class Empleado(Persona):
    def __init__(self, doc, nombre, email, id_corp, cargo="Asesor"):
        super().__init__(doc, nombre, email); self.id_corp, self.cargo = id_corp, cargo
    def info(self): return f"[EMP] {self.nombre} | {self.doc} | {self.id_corp} | {self.cargo}"

class Cliente(Persona):
    def __init__(self, doc, nombre, email, puntaje):
        super().__init__(doc, nombre, email)
        self.puntaje, self._productos, self.asesor = puntaje, [], None
    def agregar_producto(self, p): self._productos.append(p)
    def productos(self): return list(self._productos)
    def sostenibles(self): return [p for p in self._productos if isinstance(p, ICertificadoSostenible)]
    def info(self): return f"[CLI] {self.nombre} | {self.doc} | Puntaje: {self.puntaje} | Asesor: {self.asesor.nombre if self.asesor else 'N/A'}"

class ProductoFinanciero(ABC):
    _cid = 1000
    def __init__(self, nombre):
        ProductoFinanciero._cid += 1; self._id = f"PF-{ProductoFinanciero._cid}"
        self.nombre, self.activo = nombre, True
    @abstractmethod
    def calcularCostosMensuales(self): pass
    @abstractmethod
    def resumen(self): pass
    def __str__(self): return self.resumen()

class CuentaAhorros(ProductoFinanciero):
    CUOTA = 9_900.0
    def __init__(self, tasa, saldo=0.0):
        super().__init__("Cuenta Ahorros"); self._tasa = tasa; self.__s = max(saldo, 0.0)
        self._hist = HistorialMovimientos()
        if saldo: self._hist.registrar("APERTURA", saldo, self.__s)
    def saldo(self): return self.__s
    def depositar(self, m):
        if m <= 0: raise ValueError("Monto positivo requerido.")
        self.__s += m; self._hist.registrar("DEPÓSITO", m, self.__s)
    def retirar(self, m):
        if m <= 0: raise ValueError("Monto positivo requerido.")
        if m > self.__s: raise ValueError(f"Fondos insuficientes (${self.__s:,.2f})")
        self.__s -= m; self._hist.registrar("RETIRO", m, self.__s)
    def historial(self): return self._hist
    def calcularCostosMensuales(self): return self.CUOTA
    def resumen(self): return f"[{self._id}] Ahorros | ${self.__s:,.2f} | {self._tasa}%EA"

class CuentaAhorrosSostenible(CuentaAhorros, ICertificadoSostenible):
    def __init__(self, tasa, saldo=0.0, proyecto="Eco"):
        super().__init__(tasa, saldo); self.nombre = "Ahorros Sostenible"; self._proy = proyecto
    def obtener_certificado_verde(self): return f"✅ [{self._id}] Proyecto: {self._proy} | {date.today()}"
    def calcular_beneficio_tributario(self): return 15.0
    def resumen(self): return super().resumen().replace("Ahorros", "Ahorros 🌿") + f" | {self._proy}"

class TarjetaCredito(ProductoFinanciero):
    def __init__(self, cupo, corte, franquicia="VISA"):
        super().__init__("Tarjeta"); self._cupo, self.__d, self._corte, self._fra = cupo, 0.0, corte, franquicia
    def disponible(self): return self._cupo - self.__d
    def comprar(self, m):
        if m <= 0 or m > self.disponible(): raise ValueError(f"Compra inválida (disp: ${self.disponible():,.2f})")
        self.__d += m
    def pagar(self, m):
        if m <= 0: raise ValueError("Monto positivo requerido.")
        self.__d = max(0.0, self.__d - m)
    def calcularCostosMensuales(self): return self.__d * 0.0198
    def resumen(self): return f"[{self._id}] {self._fra} | Cupo: ${self._cupo:,.2f} | Deuda: ${self.__d:,.2f} | Corte: {self._corte}"

class CreditoHipotecario(ProductoFinanciero):
    def __init__(self, valor, tasa, plazo, dir_):
        super().__init__("Hipotecario"); self._v, self._t, self._p, self._dir = valor, tasa, plazo, dir_; self.__d = valor
    def pagar(self, m):
        if m <= 0: raise ValueError("Monto positivo requerido.")
        self.__d = max(0.0, self.__d - m)
    def calcularCostosMensuales(self):
        r, n = self._t/100/12, self._p*12
        return self._v/n if r==0 else self._v*r*(1+r)**n/((1+r)**n-1)
    def resumen(self): return f"[{self._id}] Hipotecario | {self._dir} | Deuda: ${self.__d:,.2f} | Cuota: ${self.calcularCostosMensuales():,.2f}/mes"

class CreditoHipotecarioBioclimatico(CreditoHipotecario, ICertificadoSostenible):
    def __init__(self, valor, tasa, plazo, dir_, cert="LEED Silver"):
        super().__init__(valor, max(0.0, tasa-0.5), plazo, dir_); self.nombre = "Hipotecario Bio"; self._cert = cert
    def obtener_certificado_verde(self): return f"✅ [{self._id}] Cert: {self._cert} | {self._dir} | {date.today()}"
    def calcular_beneficio_tributario(self): return 20.0
    def resumen(self): return super().resumen().replace("Hipotecario", "Hipotecario 🌿") + f" | {self._cert}"

class Gestor:
    def __init__(self): self._c = {}; self._e = {}
    def add_emp(self, e): self._e[e.doc] = e
    def add_cli(self, c): self._c[c.doc] = c
    def clientes(self): return list(self._c.values())
    def empleados(self): return list(self._e.values())
    def sostenibles(self): return [p for c in self._c.values() for p in c.sostenibles()]
    def costos(self):
        print("\n── COSTOS MENSUALES ──")
        for c in self._c.values():
            print(f"\n  {c.nombre}:"); total = 0
            for p in c.productos(): costo = p.calcularCostosMensuales(); total += costo; print(f"    {p.nombre:<30} ${costo:>12,.2f}")
            print(f"    {'TOTAL':<30} ${total:>12,.2f}")

def inp(p, req=True):
    while True:
        v = input(f"  {p}: ").strip()
        if v or not req: return v
        print("  ⚠ Requerido.")

def inp_f(p, mn=0.0, mx=1e9):
    while True:
        try:
            v = float(input(f"  {p}: ").replace(",","."))
            if mn<=v<=mx: return v
            print(f"  ⚠ Entre {mn} y {mx}.")
        except ValueError: print("  ⚠ Número inválido.")

def inp_i(p, mn=0, mx=999999):
    while True:
        try:
            v = int(input(f"  {p}: "))
            if mn<=v<=mx: return v
            print(f"  ⚠ Entre {mn} y {mx}.")
        except ValueError: print("  ⚠ Entero inválido.")

def elegir(titulo, ops):
    print(f"\n  {titulo}:")
    for i,o in enumerate(ops,1): print(f"  [{i}] {o}")
    while True:
        try:
            s=int(input("  Opción: "))
            if 1<=s<=len(ops): return ops[s-1]
            print("  ⚠ Inválido.")
        except ValueError: print("  ⚠ Número.")

def sel(lista, tipo="cliente"):
    if not lista: print(f"  ⚠ Sin {tipo}s."); return None
    for i,x in enumerate(lista,1): print(f"  [{i}] {x.nombre}")
    return lista[inp_i(f"Número {tipo}",1,len(lista))-1]

def f_emp(g):
    g.add_emp(Empleado(inp("Doc"), inp("Nombre"), inp("Email"), inp("ID Corp"), inp("Cargo (Enter=Asesor)",False) or "Asesor"))
    print("  ✅ Empleado registrado.")

def f_cli(g):
    c = Cliente(inp("Doc"), inp("Nombre"), inp("Email"), inp_i("Puntaje (0-1000)",0,1000))
    emps = g.empleados()
    if emps and input("  ¿Asignar asesor? (s/n): ").lower()=="s":
        for i,e in enumerate(emps,1): print(f"  [{i}] {e.nombre}")
        c.asesor = emps[inp_i("Número",1,len(emps))-1]
    g.add_cli(c); print("  ✅ Cliente registrado.")

def f_prod(g):
    c = sel(g.clientes()); 
    if not c: return
    tipos = ["Ahorros","Ahorros Sostenible 🌿","Tarjeta","Hipotecario","Hipotecario Bioclimático 🌿"]
    t = elegir("Producto", tipos); p = None
    if   t==tipos[0]: p = CuentaAhorros(inp_f("Tasa%",0,50), inp_f("Saldo inicial",0))
    elif t==tipos[1]: p = CuentaAhorrosSostenible(inp_f("Tasa%",0,50), inp_f("Saldo inicial",0), inp("Proyecto"))
    elif t==tipos[2]: p = TarjetaCredito(inp_f("Cupo",1000), inp_i("Día corte",1,28), elegir("Franquicia",["VISA","MASTERCARD","AMEX"]))
    elif t==tipos[3]: p = CreditoHipotecario(inp_f("Valor",10000), inp_f("Tasa%",0.1,30), inp_i("Plazo años",1,30), inp("Dirección"))
    elif t==tipos[4]: p = CreditoHipotecarioBioclimatico(inp_f("Valor",10000), inp_f("Tasa%",0.1,30), inp_i("Plazo años",1,30), inp("Dirección"), elegir("Certificación",["LEED Silver","LEED Gold","LEED Platinum","EDGE","BREEAM"]))
    if p: c.agregar_producto(p); print(f"  ✅ {p.resumen()}")

def f_cta(g):
    c = sel(g.clientes())
    if not c: return
    ctas = [p for p in c.productos() if isinstance(p, CuentaAhorros)]
    if not ctas: print("  ⚠ Sin cuentas."); return
    for i,ct in enumerate(ctas,1): print(f"  [{i}] {ct.resumen()}")
    ct = ctas[inp_i("Número cuenta",1,len(ctas))-1]
    op = elegir("Operación",["Depositar","Retirar","Historial"])
    try:
        if op=="Depositar": ct.depositar(inp_f("Monto",0.01)); print(f"  ✅ Saldo: ${ct.saldo():,.2f}")
        elif op=="Retirar": ct.retirar(inp_f("Monto",0.01)); print(f"  ✅ Saldo: ${ct.saldo():,.2f}")
        else: print(ct.historial())
    except ValueError as e: print(f"  ❌ {e}")

def f_ver(g):
    c = sel(g.clientes())
    if not c: return
    print(f"\n  {c.info()}")
    for p in c.productos(): print(f"    • {p.resumen()}")
    for s in c.sostenibles(): print(f"    🌿 {s.obtener_certificado_verde()} | {s.calcular_beneficio_tributario()}%")

def f_sost(g):
    ps = g.sostenibles()
    print(f"\n  Sostenibles: {len(ps)}" if ps else "  Sin productos sostenibles.")
    for s in ps: print(f"  {s.obtener_certificado_verde()} | {s.calcular_beneficio_tributario()}%")

def demo(g):
    e1=Empleado("E001","Valentina Ríos","vrios@banco.com","BC-4521","Asesora Senior")
    e2=Empleado("E002","Andrés Mora","amora@banco.com","BC-7834","Asesor Hipotecario")
    g.add_emp(e1); g.add_emp(e2)
    c1=Cliente("1020345678","Sofía Martínez","sofia@gmail.com",780); c1.asesor=e1
    ct=CuentaAhorros(3.5,2_500_000); ct.depositar(500_000); ct.retirar(150_000)
    tj=TarjetaCredito(8_000_000,15,"VISA"); tj.comprar(2_300_000)
    for p in (ct,tj,CuentaAhorrosSostenible(4.0,1_000_000,"Paneles Solares Medellín")): c1.agregar_producto(p)
    g.add_cli(c1)
    c2=Cliente("79456123","Juan Herrera","jherrera@outlook.com",850); c2.asesor=e2
    c2.agregar_producto(CreditoHipotecarioBioclimatico(320_000_000,12.5,15,"Cra 45 #80-20 Medellín","LEED Gold"))
    g.add_cli(c2); print("  ✅ Demo cargado.")

def main():
    g = Gestor(); print("\n══ NEO-BANCA 2026 ══")
    if input("  ¿Cargar demo? (s/n): ").lower()=="s": demo(g)
    OPS = {"1":("Registrar empleado",lambda:f_emp(g)),"2":("Registrar cliente",lambda:f_cli(g)),
           "3":("Agregar producto",lambda:f_prod(g)),"4":("Operar cuenta ahorros",lambda:f_cta(g)),
           "5":("Ver cliente",lambda:f_ver(g)),"6":("Reporte costos",lambda:g.costos()),
           "7":("Productos sostenibles",lambda:f_sost(g)),
           "8":("Listar clientes",lambda:[print(f"  {c.info()}") for c in g.clientes()]),
           "9":("Listar empleados",lambda:[print(f"  {e.info()}") for e in g.empleados()]),"0":("Salir",None)}
    while True:
        print("\n── MENÚ ──"); [print(f"  [{k}] {d}") for k,(d,_) in OPS.items()]
        op = input("  Opción: ").strip()
        if op=="0": print("  Hasta luego."); break
        elif op in OPS: OPS[op][1]()
        else: print("  ⚠ Inválido.")

if __name__ == "__main__": main()