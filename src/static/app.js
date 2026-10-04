/* ════════════════════════════════════════════════════════
   CATÁLOGO TI — Frontend Application Logic
   Software Avanzado | USAC 2026 | Andrés Calvo 201712620
   ════════════════════════════════════════════════════════ */

// ─── Global State ──────────────────────────────────────
let token       = localStorage.getItem("token") || null;
let currentUser = JSON.parse(localStorage.getItem("user") || "null");
let catalogos   = { nivel1: [], clases: [], criticidades: [], tipos: [], secciones: [], puestos: [], usuarios: [] };
let currentPage = 0;
const PAGE_SIZE = 15;

// ─── Bootstrap ─────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initEventListeners();
    renderAuthUI();
    bootstrap();
});

async function bootstrap() {
    await cargarCatalogosAuxiliares();
    cargarKPIs();
    cargarServicios();
    cargarOrganizacion();
    if (isAdmin()) cargarUsuarios();
}

// ─── Auth Helpers ───────────────────────────────────────
const isAdmin = () => currentUser && currentUser.rol === "administrador";

function renderAuthUI() {
    const loggedIn = !!(token && currentUser);

    // Sidebar user panel
    const infoEl   = document.getElementById("userInfoSidebar");
    const loginEl  = document.getElementById("loginPromptSidebar");
    const adminEls = document.querySelectorAll(".admin-only");

    if (loggedIn) {
        infoEl.classList.remove("hidden");
        loginEl.classList.add("hidden");

        document.getElementById("sidebarUserName").textContent = currentUser.nombre || currentUser.correo;
        const avatarEl = document.getElementById("userAvatar");
        if (avatarEl) {
            avatarEl.textContent = (currentUser.nombre || currentUser.correo || "?")[0].toUpperCase();
        }

        const rolEl = document.getElementById("sidebarUserRole");
        rolEl.textContent  = currentUser.rol;
        rolEl.className    = `role-badge role-${currentUser.rol === "administrador" ? "admin" : "consulta"}`;

        if (isAdmin()) {
            adminEls.forEach(el => el.classList.remove("hidden"));
        } else {
            adminEls.forEach(el => el.classList.add("hidden"));
        }
    } else {
        infoEl.classList.add("hidden");
        loginEl.classList.remove("hidden");
        adminEls.forEach(el => el.classList.add("hidden"));
    }
}

// ─── Tab Navigation ─────────────────────────────────────
const TAB_LABELS = {
    "tab-catalogo":     "Catálogo de Servicios",
    "tab-organizacion": "Estructura Organizacional",
    "tab-usuarios":     "Gestión de Usuarios",
    "tab-reporte":      "Reporte de Calidad"
};

function initTabs() {
    document.querySelectorAll(".nav-item[data-tab]").forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item[data-tab]").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

    const btn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const pane = document.getElementById(tabId);
    if (btn)  btn.classList.add("active");
    if (pane) pane.classList.add("active");

    const label = TAB_LABELS[tabId] || tabId;
    document.getElementById("pageTitle").textContent = label;
    document.getElementById("breadcrumbCurrent").textContent = label;
}

// ─── Event Listeners ─────────────────────────────────────
function initEventListeners() {
    // Login / Logout
    document.getElementById("btnLoginOpen").onclick  = () => openModal("loginModal");
    document.getElementById("btnLoginClose").onclick = () => closeModal("loginModal");
    document.getElementById("btnLogout").onclick     = handleLogout;

    // Password toggle
    document.getElementById("btnTogglePass").onclick = () => {
        const inp = document.getElementById("loginPass");
        inp.type = inp.type === "password" ? "text" : "password";
    };

    // Quick logins
    document.getElementById("btnQuickAdmin").onclick  = () => doLogin("admin@demo.com", "admin123");
    document.getElementById("btnQuickNormal").onclick = () => doLogin("normal@demo.com", "clave");

    // Login form
    document.getElementById("loginForm").onsubmit = (e) => {
        e.preventDefault();
        doLogin(
            document.getElementById("loginEmail").value.trim(),
            document.getElementById("loginPass").value
        );
    };

    // Filters — Catálogo
    document.getElementById("btnFilter").onclick       = () => { currentPage = 0; cargarServicios(); };
    document.getElementById("btnResetFilter").onclick  = resetFilters;
    document.getElementById("btnPrevPage").onclick     = () => { if (currentPage > 0) { currentPage--; cargarServicios(); } };
    document.getElementById("btnNextPage").onclick     = () => { currentPage++; cargarServicios(); };
    document.getElementById("searchInput").addEventListener("keydown", e => { if (e.key === "Enter") { currentPage = 0; cargarServicios(); } });

    // Servicio modal
    document.getElementById("btnNuevoServicio").onclick    = () => abrirModalServicio();
    document.getElementById("btnServicioClose").onclick    = () => closeModal("servicioModal");
    document.getElementById("btnServicioCancel").onclick   = () => closeModal("servicioModal");
    document.getElementById("servicioForm").onsubmit       = handleGuardarServicio;
    document.getElementById("formSeccion").onchange        = (e) => filtrarUsuariosPorSeccion(parseInt(e.target.value) || null);

    // Ficha modal
    document.getElementById("btnFichaClose").onclick = () => closeModal("fichaModal");
    document.getElementById("btnFichaX").onclick      = () => closeModal("fichaModal");

    // Usuarios modal
    document.getElementById("btnNuevoUsuario").onclick   = () => abrirModalUsuario();
    document.getElementById("btnUsuarioClose").onclick   = () => closeModal("usuarioModal");
    document.getElementById("btnUsuarioCancel").onclick  = () => closeModal("usuarioModal");
    document.getElementById("usuarioForm").onsubmit      = handleCrearUsuario;

    // Org refresh
    document.getElementById("btnRefreshOrg").onclick = () => cargarOrganizacion();

    // Harness live execution
    const btnHarness = document.getElementById("btnRunHarness");
    if (btnHarness) btnHarness.onclick = ejecutarHarnessEnVivo;

    // Close modals on overlay click
    ["loginModal", "fichaModal", "servicioModal", "usuarioModal"].forEach(id => {
        document.getElementById(id).addEventListener("click", e => {
            if (e.target.id === id) closeModal(id);
        });
    });
}

function resetFilters() {
    ["searchInput", "filterNivel1", "filterClase", "filterCriticidad", "filterTipo", "filterActivo"]
        .forEach(id => document.getElementById(id).value = "");
    currentPage = 0;
    cargarServicios();
}

// ─── Modal Helpers ───────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.remove("hidden"); }
function closeModal(id) { document.getElementById(id).classList.add("hidden"); }

// ─── Authenticated Fetch ─────────────────────────────────
async function apiFetch(url, options = {}) {
    options.headers = options.headers || {};
    if (token) options.headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(url, options);
    if (res.status === 401 && token) {
        // Token was sent but server rejected it (expired or invalid)
        handleLogout(true);
        throw new Error("Unauthorized");
    }
    return res;
}

// ─── Auth Operations ─────────────────────────────────────
async function doLogin(username, password) {
    const btn = document.getElementById("btnLoginSubmit");
    const errEl = document.getElementById("loginError");
    errEl.classList.add("hidden");
    btn.disabled = true;
    btn.textContent = "Verificando…";

    try {
        const body = new URLSearchParams({ username, password });
        const res  = await fetch("/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body
        });

        if (!res.ok) {
            const err = await res.json();
            errEl.textContent = err.detail || "Credenciales incorrectas.";
            errEl.classList.remove("hidden");
            return;
        }

        const data    = await res.json();
        token         = data.access_token;
        currentUser   = { nombre: data.nombre, correo: data.correo, rol: data.rol };
        localStorage.setItem("token", token);
        localStorage.setItem("user", JSON.stringify(currentUser));

        closeModal("loginModal");
        renderAuthUI();
        showToast(`Bienvenido, ${currentUser.nombre || currentUser.correo} 👋`, "success");
        await cargarCatalogosAuxiliares();
        cargarKPIs();
        cargarServicios();
        cargarOrganizacion();
        if (isAdmin()) cargarUsuarios();
    } catch (e) {
        errEl.textContent = "Error de conexión con el servidor.";
        errEl.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.textContent = "Iniciar Sesión";
    }
}

function handleLogout(silent = false) {
    token       = null;
    currentUser = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    renderAuthUI();

    // Reset table cleanly without network loop
    const tbody = document.getElementById("serviciosTbody");
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">
            <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <span>Inicia sesión para consultar el catálogo de servicios</span>
        </td></tr>`;
    }

    const orgContainer = document.getElementById("orgTreeContainer");
    if (orgContainer) {
        orgContainer.innerHTML = `<div class="table-empty">
            <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <span>Inicia sesión para visualizar la jerarquía organizacional</span>
        </div>`;
    }

    // Reset KPIs
    const kpiTotal = document.getElementById("kpiTotalServicios");
    const kpiAct = document.getElementById("kpiActivos");
    if (kpiTotal) kpiTotal.textContent = "—";
    if (kpiAct) kpiAct.textContent = "—";

    if (!silent) showToast("Sesión cerrada correctamente");
}

// ─── Catálogos Auxiliares ────────────────────────────────
async function cargarCatalogosAuxiliares() {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const safeGet = async (url) => {
        try { const r = await fetch(url, { headers }); return r.ok ? r.json() : []; }
        catch (_) { return []; }
    };

    const [n1, cl, cr, tp, sec, pue, us] = await Promise.all([
        safeGet("/servicios-nivel1/"),
        safeGet("/clases/"),
        safeGet("/criticidades/"),
        safeGet("/tipos/"),
        safeGet("/secciones/"),
        safeGet("/puestos/"),
        safeGet("/usuarios/")
    ]);

    catalogos = { nivel1: n1, clases: cl, criticidades: cr, tipos: tp, secciones: sec, puestos: pue, usuarios: us };

    poblarSelectsFiltros();
    poblarSelectsFormulario();
    poblarSelectsPuestos();
}

function poblarSelect(id, items, valKey, labelKey, placeholder, showCode = false) {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = placeholder ? `<option value="">${placeholder}</option>` : "";
    items.forEach(it => {
        const lbl = showCode && it.codigo ? `${it.codigo} — ${it[labelKey]}` : it[labelKey];
        sel.innerHTML += `<option value="${it[valKey]}">${lbl}</option>`;
    });
}

function poblarSelectsFiltros() {
    poblarSelect("filterNivel1",    catalogos.nivel1,       "id", "nombre", "Todos Nivel 1",      true);
    poblarSelect("filterClase",     catalogos.clases,       "id", "nombre", "Todas las Clases");
    poblarSelect("filterCriticidad",catalogos.criticidades, "id", "nombre", "Toda Criticidad");
    poblarSelect("filterTipo",      catalogos.tipos,        "id", "nombre", "Todos los Tipos");
}

function poblarSelectsFormulario() {
    poblarSelect("formNivel1",    catalogos.nivel1,       "id", "nombre", "— Selecciona Nivel 1 —", true);
    poblarSelect("formClase",     catalogos.clases,       "id", "nombre", "— Sin clase —");
    poblarSelect("formCriticidad",catalogos.criticidades, "id", "nombre", "— Sin criticidad —");
    poblarSelect("formTipo",      catalogos.tipos,        "id", "nombre", "— Sin tipo —");
    poblarSelect("formSeccion",   catalogos.secciones,    "id", "nombre", "— Sin sección —", true);
    poblarSelect("formUsuario",   [],                     "id", "nombre", "— Sin responsable —");
}

function poblarSelectsPuestos() {
    poblarSelect("formUsuarioPuesto", catalogos.puestos, "id", "nombre", "— Sin puesto —", true);
}

/**
 * P11: Filtrar el select de usuarios según la sección seleccionada.
 * Un usuario es válido si su puesto pertenece a la sección indicada.
 */
function filtrarUsuariosPorSeccion(seccionId) {
    const sel = document.getElementById("formUsuario");
    sel.innerHTML = '<option value="">— Sin responsable —</option>';
    if (!seccionId) return;

    // Obtener puestos de la sección
    const puestosSeccion = new Set(
        catalogos.puestos.filter(p => p.seccion_id === seccionId).map(p => p.id)
    );

    // Filtrar usuarios cuyos puestos pertenezcan a esa sección
    const usersSeccion = catalogos.usuarios.filter(u => u.puesto_id && puestosSeccion.has(u.puesto_id));

    if (usersSeccion.length === 0) {
        sel.innerHTML += '<option disabled>— No hay usuarios en esta sección —</option>';
        return;
    }

    usersSeccion.forEach(u => {
        sel.innerHTML += `<option value="${u.id}">${u.nombre} (${u.correo})</option>`;
    });
}

// ─── KPIs ────────────────────────────────────────────────
async function cargarKPIs() {
    // Update KPI values from catalogos (already loaded)
    document.getElementById("kpiNivel1").textContent    = catalogos.nivel1.length || "—";
    document.getElementById("kpiUsuarios").textContent  = catalogos.usuarios.length || "—";
    document.getElementById("statNivel1").textContent   = catalogos.nivel1.length || 12;

    // Services KPIs — fetch total count and active count
    if (!token) {
        document.getElementById("kpiTotalServicios").textContent = "—";
        document.getElementById("kpiActivos").textContent        = "—";
        return;
    }

    try {
        const [allRes, activeRes] = await Promise.all([
            apiFetch("/servicios/?limit=1000&skip=0"),
            apiFetch("/servicios/?limit=1000&skip=0&activo=S")
        ]);

        if (allRes.ok && activeRes.ok) {
            const all    = await allRes.json();
            const active = await activeRes.json();
            document.getElementById("kpiTotalServicios").textContent = all.length;
            document.getElementById("kpiActivos").textContent        = active.length;
            document.getElementById("statNivel2").textContent        = all.length;
        }
    } catch (_) {}
}

// ─── Servicios Table ─────────────────────────────────────
async function cargarServicios() {
    const tbody = document.getElementById("serviciosTbody");
    if (!token) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">
            <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <span>Inicia sesión para consultar el catálogo de servicios</span>
        </td></tr>`;
        return;
    }
    tbody.innerHTML = '<tr><td colspan="10" class="table-empty"><div class="spinner"></div><span>Consultando catálogo…</span></td></tr>';

    const params = new URLSearchParams();
    const q  = document.getElementById("searchInput").value.trim();
    const n1 = document.getElementById("filterNivel1").value;
    const cl = document.getElementById("filterClase").value;
    const cr = document.getElementById("filterCriticidad").value;
    const tp = document.getElementById("filterTipo").value;
    const ac = document.getElementById("filterActivo").value;

    if (q)  params.append("q",            q);
    if (n1) params.append("nivel1_id",    n1);
    if (cl) params.append("clase_id",     cl);
    if (cr) params.append("criticidad_id",cr);
    if (tp) params.append("tipo_id",      tp);
    if (ac) params.append("activo",       ac);

    params.append("skip",  currentPage * PAGE_SIZE);
    params.append("limit", PAGE_SIZE);

    try {
        const res = await apiFetch(`/servicios/?${params}`);

        if (!res.ok) {
            tbody.innerHTML = `<tr><td colspan="10" class="table-empty">
                <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                <span>Inicia sesión para consultar el catálogo de servicios</span>
            </td></tr>`;
            return;
        }

        const servicios = await res.json();

        if (servicios.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" class="table-empty">
                <svg width="40" height="40" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span>No se encontraron servicios con los filtros aplicados</span>
            </td></tr>`;
            return;
        }

        tbody.innerHTML = "";
        servicios.forEach(s => {
            const estadoBadge = s.activo === "S"
                ? '<span class="badge badge-s">Activo</span>'
                : (s.activo === "N" ? '<span class="badge badge-n">Inactivo</span>' : '<span class="badge">N/A</span>');
            const rango = (s.minimo != null || s.maximo != null)
                ? `${s.metrica || ''} ${s.minimo ?? '?'} – ${s.maximo ?? '?'}`
                : '<span class="text-muted">—</span>';
            const responsable = s.seccion_nombre
                ? `${s.seccion_nombre}${s.usuario_nombre ? ` / ${s.usuario_nombre}` : ''}`
                : '<span class="text-muted">—</span>';

            const adminActions = isAdmin() ? `
                <button class="btn-icon" onclick="editarServicio(${s.id})" title="Editar">✏️</button>
                <button class="btn-icon btn-icon-danger" onclick="desactivarServicio(${s.id})" title="Dar de baja lógica">🗑️</button>
            ` : "";

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong style="font-family:monospace;font-size:13px;">${s.codigo}</strong></td>
                <td style="max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${s.nombre}">${s.nombre}</td>
                <td>${s.nivel1_nombre || '<span class="text-muted">—</span>'}</td>
                <td>${s.clase_nombre || '<span class="text-muted">—</span>'}</td>
                <td>${s.criticidad_nombre || '<span class="text-muted">—</span>'}</td>
                <td>${s.tipo_nombre || '<span class="text-muted">—</span>'}</td>
                <td style="font-size:12px;">${rango}</td>
                <td>${estadoBadge}</td>
                <td style="font-size:12px;">${responsable}</td>
                <td>
                    <div class="action-group-table">
                        <button class="btn-icon btn-icon-view" onclick="verFicha(${s.id})" title="Ver ficha técnica">📋</button>
                        ${adminActions}
                    </div>
                </td>`;
            tbody.appendChild(tr);
        });

        const from = currentPage * PAGE_SIZE + 1;
        const to   = from + servicios.length - 1;
        document.getElementById("pageInfo").textContent       = `Mostrando ${from}–${to}`;
        document.getElementById("pageNumberBadge").textContent = currentPage + 1;
        document.getElementById("btnPrevPage").disabled        = currentPage === 0;
        document.getElementById("btnNextPage").disabled        = servicios.length < PAGE_SIZE;

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">
            <span>Error al cargar servicios. Inicia sesión primero.</span>
        </td></tr>`;
    }
}

// ─── Ficha Modal ─────────────────────────────────────────
async function verFicha(id) {
    openModal("fichaModal");
    document.getElementById("fichaBody").innerHTML = '<div class="table-empty"><div class="spinner"></div></div>';

    try {
        const res = await apiFetch(`/servicios/${id}`);
        if (!res.ok) { closeModal("fichaModal"); return; }
        const s = await res.json();

        document.getElementById("fichaTitle").textContent = `${s.codigo} — ${s.nombre}`;

        const item = (label, val, full = false) => `
            <div class="ficha-item${full ? ' span-full' : ''}">
                <span class="ficha-label">${label}</span>
                <div class="ficha-val">${val ?? '<span class="text-muted">N/A</span>'}</div>
            </div>`;

        const estadoHtml = s.activo === "S"
            ? '<span class="badge badge-s">Activo</span>'
            : (s.activo === "N" ? '<span class="badge badge-n">Inactivo</span>' : '<span class="badge">Desconocido</span>');

        document.getElementById("fichaBody").innerHTML = `
            ${item("Código (N2)",           `<code>${s.codigo}</code>`)}
            ${item("Estado",                estadoHtml)}
            ${item("Servicio Nivel 1",      s.nivel1_nombre)}
            ${item("Clase de Servicio",     s.clase_nombre)}
            ${item("Criticidad",            s.criticidad_nombre)}
            ${item("Tipo de Servicio",      s.tipo_nombre)}
            ${item("Métrica",               s.metrica)}
            ${item("Umbral Mínimo",         s.minimo ?? null)}
            ${item("Umbral Máximo",         s.maximo ?? null)}
            ${item("Sección Responsable",   s.seccion_nombre)}
            ${item("Usuario Responsable",   s.usuario_nombre)}
            ${item("Nombre del Servicio",   s.nombre, true)}
            ${item("Descripción",           s.descripcion || "<em>Sin descripción</em>", true)}
        `;
    } catch (_) {
        closeModal("fichaModal");
        showToast("Error al obtener ficha técnica", "error");
    }
}

// ─── Crear / Editar Servicio ─────────────────────────────
function abrirModalServicio(servicio = null) {
    document.getElementById("servicioModalTitle").textContent = servicio ? `Editar Servicio ${servicio.codigo}` : "Crear Nuevo Servicio";
    document.getElementById("formServicioId").value    = servicio?.id || "";
    document.getElementById("formCodigo").value        = servicio?.codigo || "";
    document.getElementById("formCodigo").readOnly     = !!servicio;
    document.getElementById("formNombre").value        = servicio?.nombre || "";
    document.getElementById("formNivel1").value        = servicio?.nivel1_id || "";
    document.getElementById("formClase").value         = servicio?.clase_id || "";
    document.getElementById("formCriticidad").value    = servicio?.criticidad_id || "";
    document.getElementById("formTipo").value          = servicio?.tipo_id || "";
    document.getElementById("formMetrica").value       = servicio?.metrica || "";
    document.getElementById("formMinimo").value        = servicio?.minimo ?? "";
    document.getElementById("formMaximo").value        = servicio?.maximo ?? "";
    document.getElementById("formDescripcion").value   = servicio?.descripcion || "";
    document.getElementById("formActivo").value        = servicio?.activo || "S";
    document.getElementById("formServicioError").classList.add("hidden");

    // Handle section → user relationship
    const seccionId = servicio?.seccion_id || null;
    document.getElementById("formSeccion").value = seccionId || "";
    filtrarUsuariosPorSeccion(seccionId);
    setTimeout(() => {
        document.getElementById("formUsuario").value = servicio?.usuario_id || "";
    }, 50);

    openModal("servicioModal");
}

async function editarServicio(id) {
    try {
        const res = await apiFetch(`/servicios/${id}`);
        if (!res.ok) return;
        abrirModalServicio(await res.json());
    } catch (_) {
        showToast("Error al cargar servicio para edición", "error");
    }
}

async function handleGuardarServicio(e) {
    e.preventDefault();
    const errEl = document.getElementById("formServicioError");
    errEl.classList.add("hidden");

    const id     = document.getElementById("formServicioId").value;
    const isEdit = !!id;

    const minVal = document.getElementById("formMinimo").value;
    const maxVal = document.getElementById("formMaximo").value;
    const minimo = minVal !== "" ? parseFloat(minVal) : null;
    const maximo = maxVal !== "" ? parseFloat(maxVal) : null;

    // Client-side P09 validation
    if (minimo !== null && maximo !== null && minimo > maximo) {
        errEl.textContent = "⚠ Error P09: El umbral mínimo no puede ser mayor que el máximo.";
        errEl.classList.remove("hidden");
        return;
    }

    const payload = {
        codigo:        document.getElementById("formCodigo").value.trim(),
        nombre:        document.getElementById("formNombre").value.trim(),
        nivel1_id:     parseInt(document.getElementById("formNivel1").value) || null,
        clase_id:      parseInt(document.getElementById("formClase").value) || null,
        criticidad_id: parseInt(document.getElementById("formCriticidad").value) || null,
        tipo_id:       parseInt(document.getElementById("formTipo").value) || null,
        seccion_id:    parseInt(document.getElementById("formSeccion").value) || null,
        usuario_id:    parseInt(document.getElementById("formUsuario").value) || null,
        metrica:       document.getElementById("formMetrica").value.trim() || null,
        minimo,
        maximo,
        descripcion:   document.getElementById("formDescripcion").value.trim() || null,
        activo:        document.getElementById("formActivo").value
    };

    if (!payload.nivel1_id) {
        errEl.textContent = "⚠ Debes seleccionar un Servicio Nivel 1.";
        errEl.classList.remove("hidden");
        return;
    }

    try {
        const url    = isEdit ? `/servicios/${id}` : `/servicios/`;
        const method = isEdit ? "PUT" : "POST";
        const res    = await apiFetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            errEl.textContent = `⚠ ${err.detail || "Error al guardar el servicio."}`;
            errEl.classList.remove("hidden");
            return;
        }

        closeModal("servicioModal");
        showToast(`Servicio ${isEdit ? "actualizado" : "creado"} exitosamente ✓`, "success");
        await cargarCatalogosAuxiliares();
        cargarServicios();
        cargarKPIs();
    } catch (_) {
        errEl.textContent = "⚠ Error de conexión al guardar.";
        errEl.classList.remove("hidden");
    }
}

async function desactivarServicio(id) {
    if (!confirm("¿Confirmas la baja lógica de este servicio?\n\nEl registro se desactivará pero no se eliminará de la base de datos.")) return;
    try {
        const res = await apiFetch(`/servicios/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("Servicio dado de baja lógicamente ✓", "success");
            cargarServicios();
            cargarKPIs();
        } else {
            const err = await res.json();
            showToast(err.detail || "Error al dar de baja", "error");
        }
    } catch (_) {
        showToast("Error de comunicación", "error");
    }
}

// ─── Organización ────────────────────────────────────────
async function cargarOrganizacion() {
    const container = document.getElementById("orgTreeContainer");
    if (!token) {
        container.innerHTML = `<div class="table-empty">
            <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            <span>Inicia sesión para visualizar la jerarquía organizacional</span>
        </div>`;
        return;
    }
    container.innerHTML = '<div class="table-empty"><div class="spinner"></div><span>Cargando jerarquía…</span></div>';

    try {
        const [eR, aR, dR, sR, pR, uR] = await Promise.all([
            apiFetch("/empresas/"),
            apiFetch("/areas/"),
            apiFetch("/departamentos/"),
            apiFetch("/secciones/"),
            apiFetch("/puestos/"),
            apiFetch("/usuarios/")
        ]);

        if (!eR.ok) {
            container.innerHTML = `<div class="table-empty">
                <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" stroke-width="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                <span>Inicia sesión para visualizar la jerarquía organizacional</span>
            </div>`;
            return;
        }

        const [empresas, areas, deptos, secciones, puestos, usuarios] = await Promise.all([
            eR.json(), aR.json(), dR.json(), sR.json(), pR.json(), uR.json()
        ]);

        if (empresas.length === 0) {
            container.innerHTML = '<div class="table-empty"><span>No hay empresas registradas aún.</span></div>';
            return;
        }

        const buildChildren = (children) => children.length === 0 ? "" : `<div class="org-node-children">${children.join("")}</div>`;

        const nodes = empresas.map(emp => {
            const areasEmp = areas.filter(a => a.empresa_id === emp.id);
            const areaNodes = areasEmp.map(area => {
                const deptosArea = deptos.filter(d => d.area_id === area.id);
                const deptoNodes = deptosArea.map(dep => {
                    const secsDeptos = secciones.filter(s => s.departamento_id === dep.id);
                    const secNodes = secsDeptos.map(sec => {
                        const puesSec = puestos.filter(p => p.seccion_id === sec.id);
                        const pueNodes = puesSec.map(pue => {
                            const usrsPue = usuarios.filter(u => u.puesto_id === pue.id);
                            const usrNodes = usrsPue.map(u => `
                                <div class="org-node">
                                    <div class="org-node-header" style="cursor:default;">
                                        <span class="org-node-icon">👤</span>
                                        <span class="org-node-label">${u.nombre}</span>
                                        <span class="org-node-code">${u.correo}</span>
                                        <span class="badge badge-${u.rol === 'administrador' ? 'admin' : 'consulta'}">${u.rol}</span>
                                        ${u.activo ? '' : '<span class="badge badge-n">Inactivo</span>'}
                                    </div>
                                </div>`).join("");
                            return `<div class="org-node"><div class="org-node-header"><span class="org-node-icon">💼</span><span class="org-node-label">${pue.nombre}</span><span class="org-node-code">${pue.codigo}</span></div>${buildChildren([usrNodes])}</div>`;
                        });
                        return `<div class="org-node"><div class="org-node-header"><span class="org-node-icon">📑</span><span class="org-node-label">${sec.nombre}</span><span class="org-node-code">${sec.codigo}</span></div>${buildChildren(pueNodes)}</div>`;
                    });
                    return `<div class="org-node"><div class="org-node-header"><span class="org-node-icon">🏬</span><span class="org-node-label">${dep.nombre}</span><span class="org-node-code">${dep.codigo}</span></div>${buildChildren(secNodes)}</div>`;
                });
                return `<div class="org-node"><div class="org-node-header"><span class="org-node-icon">📁</span><span class="org-node-label">${area.nombre}</span><span class="org-node-code">${area.codigo}</span></div>${buildChildren(deptoNodes)}</div>`;
            });
            return `<div class="org-node"><div class="org-node-header" style="background:#f0f4ff;border-radius:8px;padding:12px 16px;"><span class="org-node-icon">🏢</span><span class="org-node-label" style="font-size:15px;">${emp.nombre}</span><span class="org-node-code">${emp.codigo}</span></div>${buildChildren(areaNodes)}</div>`;
        });

        container.innerHTML = `<div class="org-tree">${nodes.join("")}</div>`;

    } catch (_) {
        container.innerHTML = '<div class="table-empty"><span>Inicia sesión para explorar la jerarquía organizacional.</span></div>';
    }
}

// ─── Usuarios Tab ────────────────────────────────────────
async function cargarUsuarios() {
    const tbody = document.getElementById("usuariosTbody");
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="table-empty"><div class="spinner"></div></td></tr>';

    if (!token) {
        tbody.innerHTML = '<tr><td colspan="7" class="table-empty"><span>Inicia sesión para gestionar usuarios</span></td></tr>';
        return;
    }

    try {
        const res = await apiFetch("/usuarios/");
        if (!res.ok) return;
        const usuarios = await res.json();

        tbody.innerHTML = "";
        usuarios.forEach((u, i) => {
            const puestoNombre = catalogos.puestos.find(p => p.id === u.puesto_id)?.nombre || "—";
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="text-muted">${i + 1}</span></td>
                <td><strong>${u.nombre}</strong></td>
                <td>${u.correo}</td>
                <td><span class="badge badge-${u.rol === 'administrador' ? 'admin' : 'consulta'}">${u.rol}</span></td>
                <td>${puestoNombre}</td>
                <td>${u.activo ? '<span class="badge badge-s">Activo</span>' : '<span class="badge badge-n">Inactivo</span>'}</td>
                <td>
                    ${u.correo !== currentUser?.correo && isAdmin() ? `
                    <button class="btn-icon btn-icon-danger" onclick="desactivarUsuario(${u.id})" title="Desactivar usuario">🗑️</button>` : '<span class="text-muted">—</span>'}
                </td>`;
            tbody.appendChild(tr);
        });
    } catch (_) {
        tbody.innerHTML = '<tr><td colspan="7" class="table-empty"><span>Error al cargar usuarios</span></td></tr>';
    }
}

function abrirModalUsuario() {
    document.getElementById("usuarioForm").reset();
    document.getElementById("formUsuarioError").classList.add("hidden");
    openModal("usuarioModal");
}

async function handleCrearUsuario(e) {
    e.preventDefault();
    const errEl = document.getElementById("formUsuarioError");
    errEl.classList.add("hidden");

    const payload = {
        nombre:   document.getElementById("formUsuarioNombre").value.trim(),
        correo:   document.getElementById("formUsuarioCorreo").value.trim(),
        password: document.getElementById("formUsuarioPassword").value,
        rol:      document.getElementById("formUsuarioRol").value,
        puesto_id:parseInt(document.getElementById("formUsuarioPuesto").value) || null,
        activo:   true
    };

    try {
        const res = await apiFetch("/usuarios/", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            errEl.textContent = `⚠ ${err.detail || "Error al crear el usuario."}`;
            errEl.classList.remove("hidden");
            return;
        }

        closeModal("usuarioModal");
        showToast("Usuario creado exitosamente ✓", "success");
        await cargarCatalogosAuxiliares();
        cargarUsuarios();
        cargarKPIs();
    } catch (_) {
        errEl.textContent = "⚠ Error de conexión.";
        errEl.classList.remove("hidden");
    }
}

async function desactivarUsuario(id) {
    if (!confirm("¿Confirmas la desactivación de este usuario?\n\nEl registro se mantiene en la base de datos.")) return;
    try {
        const res = await apiFetch(`/usuarios/${id}`, { method: "DELETE" });
        if (res.ok) {
            showToast("Usuario desactivado correctamente ✓", "success");
            await cargarCatalogosAuxiliares();
            cargarUsuarios();
            cargarKPIs();
        } else {
            const err = await res.json();
            showToast(err.detail || "Error al desactivar usuario", "error");
        }
    } catch (_) {
        showToast("Error de comunicación", "error");
    }
}

// ─── Toast ───────────────────────────────────────────────
function showToast(msg, type = "info") {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.className   = `toast toast-${type}`;
    t.classList.remove("hidden");
    clearTimeout(t._timeout);
    t._timeout = setTimeout(() => t.classList.add("hidden"), 4500);
}

// ─── Harness Engineering Runner ──────────────────────────
async function ejecutarHarnessEnVivo() {
    const btn = document.getElementById("btnRunHarness");
    const summaryEl = document.getElementById("harnessSummary");
    const tbody = document.getElementById("harnessTbody");

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Ejecutando Pytest…`;
    }

    try {
        const res = await fetch("/harness/ejecutar");
        if (!res.ok) throw new Error("Error en ejecución de suite");
        const data = await res.json();

        if (summaryEl) {
            summaryEl.classList.remove("hidden");
            document.getElementById("harnessSummaryTitle").textContent = 
                `${data.passed} / ${data.total} Pruebas de Aceptación Superadas (${data.cobertura} Cobertura)`;
            document.getElementById("harnessSummaryMeta").textContent = 
                `Tiempo de ejecución: ${data.duracion_segundos}s • ${data.failed} errores detectados • CLI: ${data.comando_cli}`;
        }

        if (tbody && data.criterios) {
            tbody.innerHTML = "";
            data.criterios.forEach(c => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><code>${c.codigo}</code></td>
                    <td><strong>${c.nombre}</strong></td>
                    <td><code>${c.componente}</code></td>
                    <td>${c.descripcion}</td>
                    <td><span class="badge ${c.badge}">✓ ${c.estado}</span></td>
                `;
                tbody.appendChild(tr);
            });
        }
        showToast("Suite de Pruebas P01–P12 certificada exitosamente ✓", "success");
    } catch (err) {
        showToast("Error al ejecutar suite de pruebas", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                ▶ Re-ejecutar Suite en Vivo`;
        }
    }
}

// ─── Global Exposure (for onclick handlers) ──────────────
window.verFicha              = verFicha;
window.editarServicio        = editarServicio;
window.desactivarServicio    = desactivarServicio;
window.desactivarUsuario     = desactivarUsuario;
window.ejecutarHarnessEnVivo = ejecutarHarnessEnVivo;
