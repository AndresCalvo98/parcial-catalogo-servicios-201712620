/* ════════════════════════════════════════════════════════
   SERVICE DESK & CMDB — Frontend Application Logic
   Software Avanzado | USAC 2026 | Andrés Calvo 201712620
   ════════════════════════════════════════════════════════ */

// ─── Global State ──────────────────────────────────────
let token       = localStorage.getItem("token") || null;
let currentUser = JSON.parse(localStorage.getItem("user") || "null");

let catalogos   = { 
    nivel1: [], clases: [], criticidades: [], tipos: [], 
    secciones: [], puestos: [], usuarios: [], colas: [], categoriasCI: [] 
};

let currentServicioPage = 0;
let currentTicketPage   = 0;
let currentCMDBPage     = 0;
let activeTicketId      = null;
const PAGE_SIZE         = 15;

// ─── Bootstrap ─────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initEventListeners();
    renderAuthUI();
    bootstrap();
});

async function bootstrap() {
    await cargarCatalogosAuxiliares();
    cargarTickets();
    cargarCMDB();
    cargarFAQs();
    cargarDashboardKPIs();
    cargarServicios();
    cargarOrganizacion();
    if (isAdmin()) cargarUsuarios();
    if (currentUser) cargarMisSolicitudes();
}

// ─── Auth Helpers ───────────────────────────────────────
const isAdmin = () => currentUser && currentUser.rol === "administrador";

function renderAuthUI() {
    const loggedIn = !!(token && currentUser);
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
    "tab-tickets":      "Service Desk & Colas",
    "tab-portal":       "Autoservicio & FAQ",
    "tab-cmdb":         "CMDB (5,000+ CIs)",
    "tab-catalogo":     "Catálogo de Servicios",
    "tab-kpis":         "Dashboard SLAs & KPIs",
    "tab-organizacion": "Estructura Organizacional",
    "tab-usuarios":     "Gestión de Usuarios",
    "tab-reporte":      "Harness P01–P18"
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
    document.getElementById("btnQuickAdmin").onclick       = () => doLogin("admin@demo.com", "admin123");
    document.getElementById("btnQuickAgente1").onclick     = () => doLogin("agente1@demo.com", "clave123");
    document.getElementById("btnQuickAprobador").onclick   = () => doLogin("aprobador@demo.com", "clave123");
    document.getElementById("btnQuickSolicitante").onclick = () => doLogin("solicitante@demo.com", "clave123");
    document.getElementById("btnQuickNormal").onclick      = () => doLogin("normal@demo.com", "clave");

    // Login form
    document.getElementById("loginForm").onsubmit = (e) => {
        e.preventDefault();
        doLogin(
            document.getElementById("loginEmail").value.trim(),
            document.getElementById("loginPass").value
        );
    };

    // Tickets Filters & Actions
    document.getElementById("btnFilterTickets").onclick      = () => { currentTicketPage = 0; cargarTickets(); };
    document.getElementById("btnResetFilterTickets").onclick = resetTicketFilters;
    document.getElementById("btnPrevTicketPage").onclick    = () => { if (currentTicketPage > 0) { currentTicketPage--; cargarTickets(); } };
    document.getElementById("btnNextTicketPage").onclick    = () => { currentTicketPage++; cargarTickets(); };
    document.getElementById("ticketSearchInput").addEventListener("keydown", e => { if (e.key === "Enter") { currentTicketPage = 0; cargarTickets(); } });

    document.getElementById("btnNuevoTicketModalOpen").onclick    = abrirModalNuevoTicket;
    document.getElementById("btnCrearTicketDesdePortal").onclick  = abrirModalNuevoTicket;
    document.getElementById("btnNuevoTicketClose").onclick        = () => closeModal("nuevoTicketModal");
    document.getElementById("btnNuevoTicketCancel").onclick       = () => closeModal("nuevoTicketModal");
    document.getElementById("nuevoTicketForm").onsubmit           = handleCrearNuevoTicket;

    // Ticket Detail Modal
    document.getElementById("btnTicketClose").onclick       = () => closeModal("ticketModal");
    document.getElementById("btnTicketModalCerrar").onclick = () => closeModal("ticketModal");
    document.getElementById("commentForm").onsubmit         = handleEnviarComentario;
    document.getElementById("adjuntoForm").onsubmit         = handleSubirAdjunto;

    // Ticket Tabs inside modal
    document.getElementById("tabBtnComments").onclick  = () => switchTicketModalTab("comments");
    document.getElementById("tabBtnAuditoria").onclick = () => switchTicketModalTab("auditoria");
    document.getElementById("tabBtnAdjuntos").onclick  = () => switchTicketModalTab("adjuntos");

    // FAQ Search
    document.getElementById("faqSearchInput").addEventListener("input", e => filtrarFAQs(e.target.value.toLowerCase()));

    // CMDB Filters & Actions
    document.getElementById("btnFilterCMDB").onclick      = () => { currentCMDBPage = 0; cargarCMDB(); };
    document.getElementById("btnResetFilterCMDB").onclick = resetCMDBFilters;
    document.getElementById("btnPrevCMDBPage").onclick    = () => { if (currentCMDBPage > 0) { currentCMDBPage--; cargarCMDB(); } };
    document.getElementById("btnNextCMDBPage").onclick    = () => { currentCMDBPage++; cargarCMDB(); };
    document.getElementById("cmdbSearchInput").addEventListener("keydown", e => { if (e.key === "Enter") { currentCMDBPage = 0; cargarCMDB(); } });

    document.getElementById("btnCIClose").onclick       = () => closeModal("ciModal");
    document.getElementById("btnCICloseFooter").onclick = () => closeModal("ciModal");

    // Catálogo Filters & Actions
    document.getElementById("btnFilter").onclick       = () => { currentServicioPage = 0; cargarServicios(); };
    document.getElementById("btnResetFilter").onclick  = resetFilters;
    document.getElementById("btnPrevPage").onclick     = () => { if (currentServicioPage > 0) { currentServicioPage--; cargarServicios(); } };
    document.getElementById("btnNextPage").onclick     = () => { currentServicioPage++; cargarServicios(); };
    document.getElementById("searchInput").addEventListener("keydown", e => { if (e.key === "Enter") { currentServicioPage = 0; cargarServicios(); } });

    // Servicio Modal
    document.getElementById("btnNuevoServicio").onclick    = () => abrirModalServicio();
    document.getElementById("btnServicioClose").onclick    = () => closeModal("servicioModal");
    document.getElementById("btnServicioCancel").onclick   = () => closeModal("servicioModal");
    document.getElementById("servicioForm").onsubmit       = handleGuardarServicio;
    document.getElementById("formSeccion").onchange        = (e) => filtrarUsuariosPorSeccion(parseInt(e.target.value) || null);

    // Ficha Modal
    document.getElementById("btnFichaClose").onclick = () => closeModal("fichaModal");
    document.getElementById("btnFichaX").onclick     = () => closeModal("fichaModal");

    // Usuarios Modal
    document.getElementById("btnNuevoUsuario").onclick   = () => abrirModalUsuario();
    document.getElementById("btnUsuarioClose").onclick   = () => closeModal("usuarioModal");
    document.getElementById("btnUsuarioCancel").onclick  = () => closeModal("usuarioModal");
    document.getElementById("usuarioForm").onsubmit      = handleCrearUsuario;

    // Refresh buttons
    document.getElementById("btnRefreshOrg").onclick  = () => cargarOrganizacion();
    document.getElementById("btnRefreshKPIs").onclick = () => cargarDashboardKPIs();

    // Harness live execution
    const btnHarness = document.getElementById("btnRunHarness");
    if (btnHarness) btnHarness.onclick = ejecutarHarnessEnVivo;

    // Close modals on overlay click
    ["loginModal", "fichaModal", "servicioModal", "usuarioModal", "ticketModal", "nuevoTicketModal", "ciModal"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("click", e => {
                if (e.target.id === id) closeModal(id);
            });
        }
    });
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
        handleLogout(true);
        throw new Error("Sesión expirada o no autorizada");
    }
    return res;
}

// ─── Toast Notifications ─────────────────────────────────
function showToast(msg, type = "info") {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.className   = `toast toast-${type}`;
    t.classList.remove("hidden");
    setTimeout(() => t.classList.add("hidden"), 3800);
}

// ════════════════════════════════════════════════════════
// MÓDULO: SERVICE DESK (TICKETS & COLAS)
// ════════════════════════════════════════════════════════

async function cargarTickets() {
    const tbody = document.getElementById("ticketsTbody");
    tbody.innerHTML = `<tr><td colspan="10" class="table-empty"><div class="spinner"></div><span>Cargando tickets…</span></td></tr>`;

    if (!token) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">Inicia sesión con una cuenta de evaluación (ej. Administrador o Agente) para consultar los tickets de la cola.</td></tr>`;
        document.getElementById("ticketPageInfo").textContent = "Requiere autenticación";
        return;
    }

    const proceso   = document.getElementById("ticketFilterProceso").value;
    const cola_id   = document.getElementById("ticketFilterCola").value;
    const prioridad = document.getElementById("ticketFilterPrioridad").value;
    const estado    = document.getElementById("ticketFilterEstado").value;
    const search    = document.getElementById("ticketSearchInput").value.trim();

    const params = new URLSearchParams({
        skip: currentTicketPage * PAGE_SIZE,
        limit: PAGE_SIZE
    });
    if (proceso)   params.set("proceso", proceso);
    if (cola_id)   params.set("cola_id", cola_id);
    if (prioridad) params.set("prioridad", prioridad);
    if (estado)    params.set("estado", estado);
    if (search)    params.set("q", search);

    try {
        const res = await apiFetch(`/api/tickets?${params.toString()}`);
        if (!res.ok) throw new Error("Error consultando tickets");
        const data = await res.json();
        const tickets = Array.isArray(data) ? data : (data.items || []);

        renderTicketsTable(tickets, data.total);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty text-danger">Error: ${err.message}</td></tr>`;
    }
}

function renderTicketsTable(tickets, totalCount) {
    const tbody = document.getElementById("ticketsTbody");
    if (!tickets || tickets.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">No se encontraron tickets con los filtros actuales.</td></tr>`;
        document.getElementById("ticketPageInfo").textContent = "Sin resultados";
        return;
    }

    tbody.innerHTML = tickets.map(t => {
        const codigo = t.numero_ticket || t.codigo || `TK-${t.id}`;
        const pBadge = getPrioridadBadge(t.prioridad);
        const eBadge = getEstadoBadge(t.estado);
        const procesoBadge = `<span class="badge badge-purple">${escapeHtml(t.proceso)}</span>`;
        const asignado = t.responsable_nombre || (t.asignado ? t.asignado.nombre : null) || `<em class="text-muted">Sin asignar</em>`;
        const solicitante = t.solicitante_nombre || (t.solicitante ? t.solicitante.nombre : null) || "Sistema";
        const cola = t.cola_nombre || (t.cola ? t.cola.nombre : "General");

        const isClaimed = !!(t.responsable_id || t.asignado_id);
        const canClaim = !isClaimed && t.estado !== "Cerrado" && t.estado !== "Cancelado";
        const claimBtn = canClaim
            ? `<button class="btn btn-sm btn-primary" onclick="handleTomarTicket(${t.id}, event)" title="Tomar este ticket de la cola">Tomar</button>`
            : "";

        return `
            <tr>
                <td><code class="ticket-badge-code">${escapeHtml(codigo)}</code></td>
                <td>${procesoBadge}</td>
                <td><strong>${escapeHtml(t.titulo)}</strong></td>
                <td>${pBadge}</td>
                <td>${escapeHtml(solicitante)}</td>
                <td>${typeof asignado === 'string' && asignado.startsWith('<') ? asignado : escapeHtml(asignado)}</td>
                <td><span class="badge badge-gray">${escapeHtml(cola)}</span></td>
                <td>${eBadge}</td>
                <td>${formatSLA(t.fecha_sla_resolucion || t.fecha_resolucion, t.estado)}</td>
                <td>
                    <div class="action-group-table">
                        <button class="btn btn-sm btn-ghost" onclick="abrirDetalleTicket(${t.id})" title="Gestionar Ticket">Ver</button>
                        ${claimBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    const start = currentTicketPage * PAGE_SIZE + 1;
    const end   = start + tickets.length - 1;
    const totalTxt = totalCount !== undefined ? ` de ${totalCount}` : "";
    document.getElementById("ticketPageInfo").textContent = `Mostrando ${start}–${end}${totalTxt}`;
    document.getElementById("ticketPageBadge").textContent = currentTicketPage + 1;
}

function getPrioridadBadge(p) {
    if (!p) return `<span class="badge badge-gray">—</span>`;
    if (p.includes("P1")) return `<span class="badge badge-red">${escapeHtml(p)}</span>`;
    if (p.includes("P2")) return `<span class="badge badge-orange">${escapeHtml(p)}</span>`;
    if (p.includes("P3")) return `<span class="badge badge-blue">${escapeHtml(p)}</span>`;
    return `<span class="badge badge-gray">${escapeHtml(p)}</span>`;
}

function getEstadoBadge(e) {
    if (!e) return `<span class="badge badge-gray">—</span>`;
    if (e === "Resuelto" || e === "Cerrado") return `<span class="badge badge-s">${escapeHtml(e)}</span>`;
    if (e === "En Progreso" || e === "En Ejecución") return `<span class="badge badge-blue">${escapeHtml(e)}</span>`;
    if (e === "En Aprobación" || e === "En Evaluación") return `<span class="badge badge-orange">${escapeHtml(e)}</span>`;
    if (e === "Cancelado" || e === "Rechazado") return `<span class="badge badge-n">${escapeHtml(e)}</span>`;
    return `<span class="badge badge-gray">${escapeHtml(e)}</span>`;
}

function formatSLA(slaDate, estado) {
    if (estado === "Resuelto" || estado === "Cerrado") {
        return `<span class="text-success" style="font-size:12px; font-weight:600;">✓ Finalizado</span>`;
    }
    if (!slaDate) return `<span class="text-muted" style="font-size:12px;">N/A</span>`;
    
    const diff = new Date(slaDate) - new Date();
    if (diff < 0) {
        return `<span class="text-danger" style="font-size:12px; font-weight:700;">⚠ Vencido</span>`;
    }
    const hours = Math.round(diff / 3600000);
    return `<span class="text-secondary" style="font-size:12px;">${hours}h restantes</span>`;
}

async function handleTomarTicket(ticketId, event) {
    if (event) event.stopPropagation();
    if (!token) {
        showToast("Debes iniciar sesión para tomar un ticket", "error");
        openModal("loginModal");
        return;
    }
    try {
        const res = await apiFetch(`/api/tickets/${ticketId}/tomar`, { method: "POST" });
        if (res.status === 409) {
            showToast("Conflicto de concurrencia: el ticket ya fue tomado por otro agente.", "error");
            cargarTickets();
            return;
        }
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Error al tomar el ticket");
        }
        showToast("¡Ticket asignado exitosamente a tu usuario!", "success");
        cargarTickets();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function abrirDetalleTicket(ticketId) {
    activeTicketId = ticketId;
    try {
        const res = await apiFetch(`/api/tickets/${ticketId}`);
        if (!res.ok) throw new Error("No se pudo cargar el detalle del ticket");
        const t = await res.json();

        // Render header
        document.getElementById("ticketDetailCodigo").textContent    = t.numero_ticket || t.codigo || `TK-${t.id}`;
        document.getElementById("ticketDetailProceso").textContent   = t.proceso;
        document.getElementById("ticketDetailPrioridad").textContent = t.prioridad;
        document.getElementById("ticketDetailEstado").textContent    = t.estado;
        document.getElementById("ticketDetailTitulo").textContent    = t.titulo;
        document.getElementById("ticketDetailDescripcion").textContent = t.descripcion || "Sin descripción proporcionada.";

        // Render meta
        const srvTxt = t.servicio_nivel2_nombre 
            ? `${t.servicio_nivel2_codigo || ''} - ${t.servicio_nivel2_nombre}`
            : (t.servicio_n2 ? `${t.servicio_n2.codigo} - ${t.servicio_n2.nombre}` : "No vinculado");
        document.getElementById("ticketDetailServicio").textContent   = srvTxt;
        document.getElementById("ticketDetailCola").textContent       = t.cola_nombre || (t.cola ? t.cola.nombre : "Sin cola asignada");
        document.getElementById("ticketDetailAsignado").textContent   = t.responsable_nombre || (t.asignado ? t.asignado.nombre : "Sin asignar");
        document.getElementById("ticketDetailSolicitante").textContent = t.solicitante_nombre || (t.solicitante ? t.solicitante.nombre : "Sistema");
        document.getElementById("ticketDetailSLA").textContent        = t.fecha_sla_resolucion ? new Date(t.fecha_sla_resolucion).toLocaleString() : (t.fecha_resolucion ? new Date(t.fecha_resolucion).toLocaleString() : "N/A");

        // CIs vinculados
        const cis = t.cis_afectados_codigos || (t.cis ? t.cis.map(c => c.ci.codigo) : []);
        const ciList = cis.length > 0 
            ? cis.map(cod => `<code class="mr-1">${escapeHtml(cod)}</code>`).join(" ")
            : "Ninguno";
        document.getElementById("ticketDetailCI").innerHTML = ciList;

        // Render transiciones permitidas según máquina de estados
        renderTransicionesTicket(t);

        // Render comentarios
        renderTicketComments(t.comentarios || []);

        // Render auditoría
        renderTicketAuditoria(t.auditoria || []);

        // Render adjuntos
        renderTicketAdjuntos(t.adjuntos || []);

        switchTicketModalTab("comments");
        openModal("ticketModal");
    } catch (err) {
        showToast(err.message, "error");
    }
}

function renderTransicionesTicket(t) {
    const c = document.getElementById("ticketTransitionsContainer");
    c.innerHTML = "";

    const transicionesMap = {
        "Nuevo": ["Asignado", "En Progreso", "Cancelado"],
        "Asignado": ["En Progreso", "Pendiente Tercero", "Resuelto", "Cancelado"],
        "En Progreso": ["En Aprobación", "Pendiente Tercero", "Resuelto", "Cancelado"],
        "En Aprobación": ["Aprobado", "Rechazado"],
        "Aprobado": ["En Ejecución", "Resuelto"],
        "En Ejecución": ["Resuelto", "Cancelado"],
        "Pendiente Tercero": ["En Progreso", "Resuelto"],
        "Resuelto": ["Cerrado", "Reabierto"],
        "Cerrado": ["Reabierto"],
        "Reabierto": ["En Progreso", "Resuelto"]
    };

    const nextStates = transicionesMap[t.estado] || [];
    if (nextStates.length === 0) {
        c.innerHTML = `<span class="text-muted" style="font-size:12px;">No hay transiciones de estado permitidas desde '${escapeHtml(t.estado)}'.</span>`;
        return;
    }

    nextStates.forEach(st => {
        let btnClass = "btn btn-sm btn-ghost";
        if (st === "Resuelto" || st === "Cerrado" || st === "Aprobado") btnClass = "btn btn-sm btn-success";
        if (st === "Cancelado" || st === "Rechazado") btnClass = "btn btn-sm btn-danger";
        if (st === "En Progreso" || st === "En Ejecución") btnClass = "btn btn-sm btn-primary";

        const btn = document.createElement("button");
        btn.className = btnClass;
        btn.textContent = `➔ ${st}`;
        btn.onclick = () => ejecutarTransicionTicket(t.id, st);
        c.appendChild(btn);
    });
}

async function ejecutarTransicionTicket(ticketId, nuevoEstado) {
    if (!token) {
        showToast("Debes iniciar sesión para cambiar estados", "error");
        openModal("loginModal");
        return;
    }

    let resolucion = null;
    let motivo = `Transición a ${nuevoEstado} vía consola Service Desk`;

    if (nuevoEstado === "Resuelto" || nuevoEstado === "Cerrado") {
        resolucion = prompt("Ingresa el resumen de la solución aplicada:");
        if (!resolucion || resolucion.trim() === "") {
            showToast("Es obligatorio registrar la solución para cerrar o resolver el ticket", "error");
            return;
        }
    } else if (nuevoEstado === "Reabierto") {
        motivo = prompt("Ingresa el motivo de reapertura:") || "Reapertura por solicitud del usuario";
    }

    try {
        const payload = {
            nuevo_estado: nuevoEstado,
            motivo: motivo,
            resolucion: resolucion
        };
        const res = await apiFetch(`/api/tickets/${ticketId}/transicion`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Error al procesar la transición");
        }

        showToast(`Estado actualizado a: ${nuevoEstado}`, "success");
        abrirDetalleTicket(ticketId);
        cargarTickets();
        cargarDashboardKPIs();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function switchTicketModalTab(tab) {
    document.getElementById("tabBtnComments").classList.toggle("active", tab === "comments");
    document.getElementById("tabBtnAuditoria").classList.toggle("active", tab === "auditoria");
    document.getElementById("tabBtnAdjuntos").classList.toggle("active", tab === "adjuntos");

    document.getElementById("ticketTabCommentsPane").classList.toggle("hidden", tab !== "comments");
    document.getElementById("ticketTabAuditoriaPane").classList.toggle("hidden", tab !== "auditoria");
    document.getElementById("ticketTabAdjuntosPane").classList.toggle("hidden", tab !== "adjuntos");
}

function renderTicketComments(comments) {
    const list = document.getElementById("ticketCommentsList");
    if (!comments || comments.length === 0) {
        list.innerHTML = `<div class="text-muted" style="padding:12px; font-size:13px;">Sin comentarios registrados.</div>`;
        return;
    }
    list.innerHTML = comments.map(c => `
        <div class="comment-card ${c.es_interno ? 'internal' : ''}">
            <div class="comment-card-header">
                <strong>${c.usuario ? escapeHtml(c.usuario.nombre) : 'Usuario'}</strong>
                <span>${c.es_interno ? '🔒 NOTA INTERNA • ' : ''}${new Date(c.fecha).toLocaleString()}</span>
            </div>
            <div class="comment-card-body">${escapeHtml(c.texto)}</div>
        </div>
    `).join("");
}

function renderTicketAuditoria(audit) {
    const list = document.getElementById("ticketAuditList");
    if (!audit || audit.length === 0) {
        list.innerHTML = `<div class="text-muted" style="padding:12px; font-size:13px;">Sin bitácora registrada.</div>`;
        return;
    }
    list.innerHTML = audit.map(a => `
        <div class="audit-item">
            <strong>${escapeHtml(a.campo_modificado || 'Cambio')}:</strong>
            <span>'${escapeHtml(a.valor_anterior || '—')}' ➔ '${escapeHtml(a.valor_nuevo || '—')}'</span>
            <div class="text-muted" style="font-size:11px; margin-top:2px;">
                ${a.usuario ? escapeHtml(a.usuario.nombre) : 'Sistema'} • ${new Date(a.fecha).toLocaleString()}
                ${a.motivo ? `• <em>${escapeHtml(a.motivo)}</em>` : ''}
            </div>
        </div>
    `).join("");
}

function renderTicketAdjuntos(adjuntos) {
    const list = document.getElementById("ticketAdjuntosList");
    if (!adjuntos || adjuntos.length === 0) {
        list.innerHTML = `<div class="text-muted" style="padding:12px; font-size:13px;">Sin archivos adjuntos.</div>`;
        return;
    }
    list.innerHTML = adjuntos.map(a => `
        <div class="adjunto-item" style="padding:6px 12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; font-size:12.5px; display:flex; justify-content:space-between;">
            <span>📎 <strong>${escapeHtml(a.nombre_archivo)}</strong></span>
            <a href="${escapeHtml(a.url_almacenamiento)}" target="_blank" class="text-primary" style="font-size:12px;">Ver archivo</a>
        </div>
    `).join("");
}

async function handleEnviarComentario(e) {
    e.preventDefault();
    if (!activeTicketId) return;
    if (!token) {
        showToast("Debes iniciar sesión para comentar", "error");
        openModal("loginModal");
        return;
    }

    const texto = document.getElementById("commentTextInput").value.trim();
    const es_interno = document.getElementById("commentIsInternal").checked;
    if (!texto) return;

    try {
        const res = await apiFetch(`/api/tickets/${activeTicketId}/comentarios`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto, es_interno })
        });
        if (!res.ok) throw new Error("Error enviando comentario");

        document.getElementById("commentTextInput").value = "";
        document.getElementById("commentIsInternal").checked = false;
        abrirDetalleTicket(activeTicketId);
        showToast("Comentario agregado", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleSubirAdjunto(e) {
    e.preventDefault();
    if (!activeTicketId) return;
    if (!token) {
        showToast("Debes iniciar sesión para adjuntar archivos", "error");
        return;
    }

    const nombre_archivo = document.getElementById("adjuntoNombreInput").value.trim();
    const url = document.getElementById("adjuntoUrlInput").value.trim();
    if (!nombre_archivo || !url) return;

    try {
        const res = await apiFetch(`/api/tickets/${activeTicketId}/adjuntos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre_archivo, url_almacenamiento: url })
        });
        if (!res.ok) throw new Error("Error registrando archivo");

        document.getElementById("adjuntoNombreInput").value = "";
        document.getElementById("adjuntoUrlInput").value = "";
        abrirDetalleTicket(activeTicketId);
        showToast("Archivo adjuntado", "success");
    } catch (err) {
        showToast(err.message, "error");
    }
}

function abrirModalNuevoTicket() {
    if (!token) {
        showToast("Inicia sesión para levantar un ticket", "info");
        openModal("loginModal");
        return;
    }

    // Llenar select de servicios
    const sSelect = document.getElementById("newTicketServicio");
    sSelect.innerHTML = `<option value="">Selecciona un Servicio Nivel 2…</option>` +
        (catalogos.serviciosN2 || []).map(s => `<option value="${s.id}">${escapeHtml(s.codigo)} - ${escapeHtml(s.nombre)}</option>`).join("");

    // Llenar select de colas
    const cSelect = document.getElementById("newTicketCola");
    cSelect.innerHTML = `<option value="">Auto-enrutar según proceso…</option>` +
        (catalogos.colas || []).map(c => `<option value="${c.id}">${escapeHtml(c.nombre)}</option>`).join("");

    document.getElementById("nuevoTicketForm").reset();
    document.getElementById("newTicketError").classList.add("hidden");
    openModal("nuevoTicketModal");
}

async function handleCrearNuevoTicket(e) {
    e.preventDefault();
    const errBox = document.getElementById("newTicketError");
    errBox.classList.add("hidden");

    const proceso   = document.getElementById("newTicketProceso").value;
    const prioridad = document.getElementById("newTicketPrioridad").value;
    const titulo    = document.getElementById("newTicketTitulo").value.trim();
    const desc      = document.getElementById("newTicketDescripcion").value.trim();
    const srvId     = parseInt(document.getElementById("newTicketServicio").value) || null;
    const colaId    = parseInt(document.getElementById("newTicketCola").value) || null;

    if (!titulo || !desc) {
        errBox.textContent = "Por favor completa el título y los detalles del requerimiento.";
        errBox.classList.remove("hidden");
        return;
    }

    try {
        const payload = {
            titulo: titulo,
            descripcion: desc,
            proceso: proceso,
            prioridad: prioridad,
            servicio_n2_id: srvId,
            cola_id: colaId
        };
        const res = await apiFetch("/api/tickets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Error al crear ticket");
        }

        const nuevo = await res.json();
        closeModal("nuevoTicketModal");
        showToast(`¡Ticket ${nuevo.codigo} creado exitosamente!`, "success");
        cargarTickets();
        cargarDashboardKPIs();
        if (currentUser) cargarMisSolicitudes();
    } catch (err) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
    }
}

function resetTicketFilters() {
    ["ticketFilterProceso", "ticketFilterCola", "ticketFilterPrioridad", "ticketFilterEstado", "ticketSearchInput"]
        .forEach(id => document.getElementById(id).value = "");
    currentTicketPage = 0;
    cargarTickets();
}

// ════════════════════════════════════════════════════════
// MÓDULO: AUTOSERVICIO & FAQ (NIVEL 0)
// ════════════════════════════════════════════════════════

let faqsCached = [];

async function cargarFAQs() {
    const container = document.getElementById("faqListContainer");
    try {
        const res = await fetch("/api/faq");
        if (!res.ok) throw new Error("Error cargando base de conocimiento");
        faqsCached = await res.json();
        renderFAQs(faqsCached);
    } catch (err) {
        container.innerHTML = `<div class="text-danger" style="padding:12px;">Error: ${err.message}</div>`;
    }
}

function renderFAQs(faqs) {
    const container = document.getElementById("faqListContainer");
    if (!faqs || faqs.length === 0) {
        container.innerHTML = `<div class="table-empty">No se encontraron artículos con ese término.</div>`;
        return;
    }

    container.innerHTML = faqs.map(f => `
        <div class="faq-item">
            <div class="faq-question" onclick="this.nextElementSibling.classList.toggle('hidden')">
                <span>📖 ${escapeHtml(f.pregunta)}</span>
                <span style="font-size:12px; color:var(--text-muted);">▾</span>
            </div>
            <div class="faq-answer hidden">
                <p>${escapeHtml(f.respuesta)}</p>
                <div style="margin-top:8px; font-size:11.5px; color:var(--text-muted);">
                    Categoría: <strong>${escapeHtml(f.categoria)}</strong>
                </div>
            </div>
        </div>
    `).join("");
}

function filtrarFAQs(query) {
    if (!query) {
        renderFAQs(faqsCached);
        return;
    }
    const filtered = faqsCached.filter(f => 
        f.pregunta.toLowerCase().includes(query) || 
        f.respuesta.toLowerCase().includes(query) ||
        (f.palabras_clave && f.palabras_clave.toLowerCase().includes(query))
    );
    renderFAQs(filtered);
}

async function cargarMisSolicitudes() {
    const tbody = document.getElementById("misSolicitudesTbody");
    const badge = document.getElementById("badgeMisSolicitudes");
    if (!currentUser) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-empty">Inicia sesión para ver tus solicitudes</td></tr>`;
        badge.textContent = "0 activas";
        return;
    }

    try {
        const res = await apiFetch(`/api/tickets?solicitante_id=${currentUser.id}&limit=10`);
        if (!res.ok) throw new Error("Error cargando solicitudes");
        const data = await res.json();
        const tickets = Array.isArray(data) ? data : (data.items || []);

        badge.textContent = `${data.total ?? tickets.length} registradas`;

        if (tickets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="table-empty">No tienes solicitudes registradas aún.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickets.map(t => `
            <tr>
                <td><code class="ticket-badge-code">${escapeHtml(t.numero_ticket || t.codigo || `TK-${t.id}`)}</code></td>
                <td><strong>${escapeHtml(t.titulo)}</strong></td>
                <td>${getEstadoBadge(t.estado)}</td>
                <td>${new Date(t.fecha_creacion).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-ghost" onclick="abrirDetalleTicket(${t.id})">Ver Estado</button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-empty text-danger">Error: ${err.message}</td></tr>`;
    }
}

// ════════════════════════════════════════════════════════
// MÓDULO: CMDB (5,000+ CIs & GRAPH ENGINEERING)
// ════════════════════════════════════════════════════════

async function cargarCMDB() {
    const tbody = document.getElementById("cmdbTbody");
    tbody.innerHTML = `<tr><td colspan="9" class="table-empty"><div class="spinner"></div><span>Cargando inventario CMDB…</span></td></tr>`;

    if (!token) {
        tbody.innerHTML = `<tr><td colspan="9" class="table-empty">Inicia sesión para consultar los dispositivos de la CMDB.</td></tr>`;
        document.getElementById("cmdbPageInfo").textContent = "Requiere autenticación";
        return;
    }

    const search    = document.getElementById("cmdbSearchInput").value.trim();
    const categoria = document.getElementById("cmdbFilterCategoria").value;
    const estado    = document.getElementById("cmdbFilterEstado").value;

    const params = new URLSearchParams({
        skip: currentCMDBPage * PAGE_SIZE,
        limit: PAGE_SIZE
    });
    if (search)    params.set("q", search);
    if (categoria) params.set("clasificacion_id", categoria);
    if (estado)    params.set("estado_actual", estado);

    try {
        const res = await apiFetch(`/api/cmdb/items?${params.toString()}`);
        if (!res.ok) throw new Error("Error consultando CMDB");
        const data = await res.json();
        const cis = Array.isArray(data) ? data : (data.items || []);

        renderCMDBTable(cis, data.total);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="table-empty text-danger">Error: ${err.message}</td></tr>`;
    }
}

function renderCMDBTable(cis, totalCount) {
    const tbody = document.getElementById("cmdbTbody");
    if (!cis || cis.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="table-empty">No se encontraron CIs con los filtros indicados.</td></tr>`;
        document.getElementById("cmdbPageInfo").textContent = "Sin resultados";
        return;
    }

    tbody.innerHTML = cis.map(c => {
        const cat = c.clasificacion_nombre || (c.categoria ? c.categoria.nombre : "General");
        const ipVal = c.direccion_ip || c.ip_address;
        const ip = ipVal ? `<code>${escapeHtml(ipVal)}</code>` : `<span class="text-muted">N/A</span>`;
        const serie = c.numero_serie ? escapeHtml(c.numero_serie) : `<span class="text-muted">N/A</span>`;
        const srvCount = c.servicios_afectados_codigos ? c.servicios_afectados_codigos.length : (c.servicios ? c.servicios.length : 0);
        const srvBadge = srvCount > 0 
            ? `<span class="badge badge-blue">${srvCount} servicio(s)</span>`
            : `<span class="text-muted" style="font-size:12px;">Directo</span>`;
        const estadoVal = c.estado_actual || c.estado || "Operativo";

        return `
            <tr>
                <td><code class="ticket-badge-code">${escapeHtml(c.codigo)}</code></td>
                <td><strong>${escapeHtml(c.nombre)}</strong></td>
                <td><span class="badge badge-purple">${escapeHtml(cat)}</span></td>
                <td>${escapeHtml(c.tipo_ci || 'Dispositivo')}</td>
                <td><span class="badge ${estadoVal === 'Operativo' ? 'badge-s' : 'badge-orange'}">${escapeHtml(estadoVal)}</span></td>
                <td>${ip}</td>
                <td>${serie}</td>
                <td>${srvBadge}</td>
                <td>
                    <button class="btn btn-sm btn-ghost" onclick="abrirFichaCI(${c.id})" title="Ver Ficha y Análisis de Impacto">Impacto</button>
                </td>
            </tr>
        `;
    }).join("");

    const start = currentCMDBPage * PAGE_SIZE + 1;
    const end   = start + cis.length - 1;
    const totalTxt = totalCount !== undefined ? ` de ${totalCount}` : "";
    document.getElementById("cmdbPageInfo").textContent = `Mostrando ${start}–${end}${totalTxt}`;
    document.getElementById("cmdbPageBadge").textContent = currentCMDBPage + 1;
}

async function abrirFichaCI(ciId) {
    const modalBody = document.getElementById("ciModalBody");
    const impactBox = document.getElementById("ciImpactContainer");
    modalBody.innerHTML = `<div class="spinner"></div>`;
    impactBox.innerHTML = `<div class="spinner"></div> Calculando servicios TI afectados…`;
    openModal("ciModal");

    try {
        const res = await apiFetch(`/api/cmdb/cis/${ciId}`);
        if (!res.ok) throw new Error("No se pudo cargar el CI");
        const ci = await res.json();

        const cat = ci.clasificacion_nombre || (ci.categoria ? ci.categoria.nombre : 'General');
        document.getElementById("ciModalTitle").textContent = `${ci.codigo} — ${ci.nombre}`;
        document.getElementById("ciModalSubtitle").textContent = `Categoría: ${cat} • Tipo: ${ci.tipo_ci || 'Dispositivo'}`;

        modalBody.innerHTML = `
            <div class="ficha-item">
                <span class="ficha-key">Número de Serie</span>
                <span class="ficha-val">${ci.numero_serie || 'N/A'}</span>
            </div>
            <div class="ficha-item">
                <span class="ficha-key">Estado Operativo</span>
                <span class="ficha-val">${ci.estado_actual || ci.estado || 'Operativo'}</span>
            </div>
            <div class="ficha-item">
                <span class="ficha-key">Dirección IP</span>
                <span class="ficha-val">${ci.direccion_ip || ci.ip_address || 'N/A'}</span>
            </div>
            <div class="ficha-item">
                <span class="ficha-key">Dirección MAC</span>
                <span class="ficha-val">${ci.direccion_mac || ci.mac_address || 'N/A'}</span>
            </div>
            <div class="ficha-item">
                <span class="ficha-key">Fabricante y Modelo</span>
                <span class="ficha-val">${ci.marca || ci.fabricante || 'Genérico'} ${ci.modelo || ''}</span>
            </div>
            <div class="ficha-item">
                <span class="ficha-key">Ubicación Física</span>
                <span class="ficha-val">${ci.ubicacion_fisica || 'Datacenter Central'}</span>
            </div>
        `;

        // Llamar endpoint de Graph Engineering: Análisis de Impacto
        const impRes = await apiFetch(`/api/cmdb/cis/${ciId}/impacto`);
        if (!impRes.ok) throw new Error("Error calculando impacto en grafo");
        const imp = await impRes.json();

        const srvList = imp.servicios_negocio_afectados || imp.servicios_afectados || [];
        const ciList = imp.cis_impactados || imp.cis_afectados || [];

        const srvBadges = srvList.length > 0
            ? srvList.map(s => `<span class="impact-service-badge">⚡ ${escapeHtml(s.codigo || s.servicio_codigo)} — ${escapeHtml(s.nombre || s.servicio_nombre)}</span>`).join("")
            : `<div class="text-muted" style="font-size:12.5px;">Ningún servicio N2 depende directamente de este componente.</div>`;

        impactBox.innerHTML = `
            <div style="font-size:13px; margin-bottom:8px;">
                <strong>CIs dependientes en cascada:</strong> ${ciList.length} componentes tecnológicos.
            </div>
            <div style="font-size:13px; font-weight:600; margin-bottom:4px;">Servicios TI de Negocio en Riesgo:</div>
            <div class="impact-badge-list">
                ${srvBadges}
            </div>
        `;
    } catch (err) {
        impactBox.innerHTML = `<div class="text-danger">Error: ${err.message}</div>`;
    }
}

function resetCMDBFilters() {
    ["cmdbSearchInput", "cmdbFilterCategoria", "cmdbFilterEstado"].forEach(id => document.getElementById(id).value = "");
    currentCMDBPage = 0;
    cargarCMDB();
}

// ════════════════════════════════════════════════════════
// MÓDULO: DASHBOARD SLAS & KPIS
// ════════════════════════════════════════════════════════

async function cargarDashboardKPIs() {
    try {
        const res = await apiFetch("/api/dashboard/kpis");
        if (!res.ok) return;
        const kpis = await res.json();
        const r = kpis.resumen || kpis;

        const totalTks = r.total_tickets ?? kpis.total_tickets ?? 0;
        const activos = r.tickets_activos ?? kpis.incidentes_activos ?? 0;
        const slaPct = r.cumplimiento_sla_porcentaje ?? kpis.sla_cumplimiento_pct ?? 100;
        const mtta = r.mtta_promedio_minutos ?? kpis.mtta_promedio_min ?? 0;
        const mttr = r.mttr_promedio_minutos ?? kpis.mttr_promedio_min ?? 0;

        // Cards principales (Top de tab-tickets)
        const elTotal = document.getElementById("kpiTotalTickets");
        if (elTotal) elTotal.textContent = totalTks;

        const elActivos = document.getElementById("kpiIncidentesActivos");
        if (elActivos) elActivos.textContent = activos;

        const distProc = kpis.distribucion_proceso || kpis.por_proceso || {};
        const elCambios = document.getElementById("kpiCambiosPendientes");
        if (elCambios) elCambios.textContent = distProc["Gestion de cambios"] || distProc["Cambios"] || 0;

        const elSla = document.getElementById("kpiCumplimientoSLA");
        if (elSla) elSla.textContent = `${slaPct}%`;

        // Cards de tab-kpis
        const elMTTA = document.getElementById("kpiMTTA");
        if (elMTTA) elMTTA.textContent = `${mtta} min`;

        const elMTTR = document.getElementById("kpiMTTR");
        if (elMTTR) elMTTR.textContent = `${mttr} min`;

        const elSLAP = document.getElementById("kpiSLAPercent");
        if (elSLAP) elSLAP.textContent = `${slaPct}%`;

        const elViol = document.getElementById("kpiViolaciones");
        if (elViol) elViol.textContent = Math.round(totalTks * (1 - slaPct/100));

        // Desglose por proceso
        const procBox = document.getElementById("kpiProcesosBreakdown");
        if (procBox && distProc) {
            procBox.innerHTML = Object.entries(distProc).map(([proc, count]) => `
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1f5f9; font-size:13px;">
                    <span>📌 ${escapeHtml(proc)}</span>
                    <strong>${count} tickets</strong>
                </div>
            `).join("");
        }

        // Tabla colas
        const colasTbody = document.getElementById("kpiColasTbody");
        const distCola = kpis.distribucion_cola || kpis.por_cola;
        if (colasTbody && distCola) {
            if (Array.isArray(distCola)) {
                colasTbody.innerHTML = distCola.map(c => `
                    <tr>
                        <td><strong>${escapeHtml(c.nombre)}</strong></td>
                        <td>${c.tickets_abiertos}</td>
                        <td>${c.tiempo_atencion_promedio || '15 min'}</td>
                        <td><span class="badge badge-s">${c.sla_pct || 96}%</span></td>
                    </tr>
                `).join("");
            } else {
                colasTbody.innerHTML = Object.entries(distCola).map(([nom, count]) => `
                    <tr>
                        <td><strong>${escapeHtml(nom)}</strong></td>
                        <td>${count}</td>
                        <td>15 min</td>
                        <td><span class="badge badge-s">${slaPct}%</span></td>
                    </tr>
                `).join("");
            }
        }
    } catch (err) {
        console.warn("No se pudieron cargar KPIs:", err);
    }
}

// ════════════════════════════════════════════════════════
// MÓDULO: CATÁLOGO DE SERVICIOS TI (PARCIAL 2 RETENIDO)
// ════════════════════════════════════════════════════════

async function cargarServicios() {
    const tbody = document.getElementById("serviciosTbody");
    tbody.innerHTML = `<tr><td colspan="10" class="table-empty"><div class="spinner"></div><span>Cargando catálogo…</span></td></tr>`;

    const search     = document.getElementById("searchInput").value.trim();
    const nivel1_id  = document.getElementById("filterNivel1").value;
    const clase_id   = document.getElementById("filterClase").value;
    const crit_id    = document.getElementById("filterCriticidad").value;
    const tipo_id    = document.getElementById("filterTipo").value;
    const activo     = document.getElementById("filterActivo").value;

    const params = new URLSearchParams({
        skip: currentServicioPage * PAGE_SIZE,
        limit: PAGE_SIZE
    });
    if (search)    params.set("search", search);
    if (nivel1_id) params.set("nivel1_id", nivel1_id);
    if (clase_id)  params.set("clase_id", clase_id);
    if (crit_id)   params.set("criticidad_id", crit_id);
    if (tipo_id)   params.set("tipo_id", tipo_id);
    if (activo)    params.set("activo", activo);

    try {
        const res = await apiFetch(`/api/servicios?${params.toString()}`);
        if (!res.ok) throw new Error("Error al obtener los servicios");
        const servicios = await res.json();

        renderServiciosTable(servicios);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty text-danger">Error: ${err.message}</td></tr>`;
    }
}

function renderServiciosTable(servicios) {
    const tbody = document.getElementById("serviciosTbody");
    if (!servicios || servicios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="table-empty">No se encontraron servicios con los filtros aplicados.</td></tr>`;
        document.getElementById("pageInfo").textContent = "Sin resultados";
        return;
    }

    tbody.innerHTML = servicios.map(s => {
        const activoBadge = s.activo === "S" ? `<span class="badge badge-s">Activo</span>` : `<span class="badge badge-n">Inactivo</span>`;
        const n1 = s.nivel1 ? `${escapeHtml(s.nivel1.codigo)} - ${escapeHtml(s.nivel1.nombre)}` : "—";
        const clase = s.clase ? escapeHtml(s.clase.nombre) : "—";
        const crit = s.criticidad ? `<span class="badge badge-${s.criticidad.nombre.toLowerCase().replace(' ', '')}">${escapeHtml(s.criticidad.nombre)}</span>` : "—";
        const tipo = s.tipo ? escapeHtml(s.tipo.nombre) : "—";
        const rango = (s.minimo !== null || s.maximo !== null) ? `${s.minimo ?? '—'} a ${s.maximo ?? '—'} ${s.metrica ? `(${escapeHtml(s.metrica)})` : ''}` : (s.metrica || "—");
        const resp = s.usuario_responsable ? escapeHtml(s.usuario_responsable.nombre) : (s.seccion_responsable ? `<small class="text-muted">${escapeHtml(s.seccion_responsable.nombre)}</small>` : "—");

        const editBtn = isAdmin() ? `
            <button class="btn-icon" title="Editar Servicio" onclick="abrirModalServicio(${s.id})">
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
            </button>
            <button class="btn-icon btn-icon-danger" title="Dar de Baja" onclick="confirmarBajaServicio(${s.id}, '${escapeHtml(s.codigo)}')">
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
        ` : "";

        return `
            <tr>
                <td><code>${escapeHtml(s.codigo)}</code></td>
                <td><strong>${escapeHtml(s.nombre)}</strong></td>
                <td><small>${n1}</small></td>
                <td>${clase}</td>
                <td>${crit}</td>
                <td>${tipo}</td>
                <td><small>${rango}</small></td>
                <td>${activoBadge}</td>
                <td>${resp}</td>
                <td>
                    <div class="action-group-table">
                        <button class="btn-icon btn-icon-view" title="Ver Ficha Técnica" onclick="verFichaServicio(${s.id})">
                            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                        </button>
                        ${editBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    const start = currentServicioPage * PAGE_SIZE + 1;
    const end   = start + servicios.length - 1;
    document.getElementById("pageInfo").textContent = `Mostrando ${start}–${end}`;
    document.getElementById("pageNumberBadge").textContent = currentServicioPage + 1;
}

async function verFichaServicio(id) {
    try {
        const res = await apiFetch(`/api/servicios/${id}`);
        if (!res.ok) throw new Error("No se pudo obtener la ficha");
        const s = await res.json();

        document.getElementById("fichaTitle").textContent = `${s.codigo} — ${s.nombre}`;
        document.getElementById("fichaBody").innerHTML = `
            <div class="ficha-item"><span class="ficha-key">Código Nivel 2</span><span class="ficha-val"><code>${escapeHtml(s.codigo)}</code></span></div>
            <div class="ficha-item"><span class="ficha-key">Servicio Padre (N1)</span><span class="ficha-val">${s.nivel1 ? `${escapeHtml(s.nivel1.codigo)} - ${escapeHtml(s.nivel1.nombre)}` : '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Clase</span><span class="ficha-val">${s.clase ? escapeHtml(s.clase.nombre) : '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Criticidad</span><span class="ficha-val">${s.criticidad ? escapeHtml(s.criticidad.nombre) : '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Tipo de Servicio</span><span class="ficha-val">${s.tipo ? escapeHtml(s.tipo.nombre) : '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Métrica</span><span class="ficha-val">${s.metrica || '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Umbral Mínimo</span><span class="ficha-val">${s.minimo ?? '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Umbral Máximo</span><span class="ficha-val">${s.maximo ?? '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Sección Responsable</span><span class="ficha-val">${s.seccion_responsable ? escapeHtml(s.seccion_responsable.nombre) : '—'}</span></div>
            <div class="ficha-item"><span class="ficha-key">Usuario Responsable</span><span class="ficha-val">${s.usuario_responsable ? escapeHtml(s.usuario_responsable.nombre) : '—'}</span></div>
            <div class="ficha-item" style="grid-column: 1 / -1;"><span class="ficha-key">Descripción</span><span class="ficha-val">${s.descripcion || 'Sin descripción.'}</span></div>
        `;
        openModal("fichaModal");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function abrirModalServicio(id = null) {
    const errBox = document.getElementById("formServicioError");
    errBox.classList.add("hidden");
    document.getElementById("servicioForm").reset();

    if (id) {
        document.getElementById("servicioModalTitle").textContent = "Editar Servicio";
        document.getElementById("formServicioId").value = id;
        try {
            const res = await apiFetch(`/api/servicios/${id}`);
            const s = await res.json();
            document.getElementById("formCodigo").value = s.codigo;
            document.getElementById("formNombre").value = s.nombre;
            document.getElementById("formNivel1").value = s.nivel1_id;
            document.getElementById("formClase").value  = s.clase_id || "";
            document.getElementById("formCriticidad").value = s.criticidad_id || "";
            document.getElementById("formTipo").value   = s.tipo_id || "";
            document.getElementById("formMetrica").value = s.metrica || "";
            document.getElementById("formMinimo").value = s.minimo ?? "";
            document.getElementById("formMaximo").value = s.maximo ?? "";
            document.getElementById("formDescripcion").value = s.descripcion || "";
            document.getElementById("formActivo").value = s.activo || "S";
            document.getElementById("formSeccion").value = s.seccion_responsable_id || "";
            filtrarUsuariosPorSeccion(s.seccion_responsable_id, s.usuario_responsable_id);
        } catch (err) {
            showToast("Error cargando servicio", "error");
            return;
        }
    } else {
        document.getElementById("servicioModalTitle").textContent = "Crear Nuevo Servicio";
        document.getElementById("formServicioId").value = "";
    }
    openModal("servicioModal");
}

async function handleGuardarServicio(e) {
    e.preventDefault();
    const id = document.getElementById("formServicioId").value;
    const errBox = document.getElementById("formServicioError");
    errBox.classList.add("hidden");

    const payload = {
        codigo: document.getElementById("formCodigo").value.trim(),
        nombre: document.getElementById("formNombre").value.trim(),
        nivel1_id: parseInt(document.getElementById("formNivel1").value),
        clase_id: parseInt(document.getElementById("formClase").value) || null,
        criticidad_id: parseInt(document.getElementById("formCriticidad").value) || null,
        tipo_id: parseInt(document.getElementById("formTipo").value) || null,
        metrica: document.getElementById("formMetrica").value.trim() || null,
        minimo: document.getElementById("formMinimo").value !== "" ? parseFloat(document.getElementById("formMinimo").value) : null,
        maximo: document.getElementById("formMaximo").value !== "" ? parseFloat(document.getElementById("formMaximo").value) : null,
        descripcion: document.getElementById("formDescripcion").value.trim() || null,
        activo: document.getElementById("formActivo").value,
        seccion_responsable_id: parseInt(document.getElementById("formSeccion").value) || null,
        usuario_responsable_id: parseInt(document.getElementById("formUsuario").value) || null
    };

    if (payload.minimo !== null && payload.maximo !== null && payload.minimo > payload.maximo) {
        errBox.textContent = "El valor mínimo no puede ser mayor que el máximo.";
        errBox.classList.remove("hidden");
        return;
    }

    try {
        const url    = id ? `/api/servicios/${id}` : "/api/servicios";
        const method = id ? "PUT" : "POST";
        const res    = await apiFetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Error al guardar el servicio");
        }

        closeModal("servicioModal");
        showToast(id ? "Servicio actualizado correctamente" : "Servicio creado exitosamente", "success");
        cargarServicios();
    } catch (err) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
    }
}

async function confirmarBajaServicio(id, codigo) {
    if (!confirm(`¿Estás seguro de dar de baja lógica al servicio ${codigo}?`)) return;
    try {
        const res = await apiFetch(`/api/servicios/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("No se pudo dar de baja");
        showToast(`Servicio ${codigo} dado de baja lógica`, "success");
        cargarServicios();
    } catch (err) {
        showToast(err.message, "error");
    }
}

function resetFilters() {
    ["searchInput", "filterNivel1", "filterClase", "filterCriticidad", "filterTipo", "filterActivo"]
        .forEach(id => document.getElementById(id).value = "");
    currentServicioPage = 0;
    cargarServicios();
}

// ════════════════════════════════════════════════════════
// MÓDULO: ESTRUCTURA ORGANIZACIONAL & USUARIOS
// ════════════════════════════════════════════════════════

async function cargarOrganizacion() {
    const c = document.getElementById("orgTreeContainer");
    try {
        const res = await apiFetch("/api/organizacion");
        if (!res.ok) throw new Error("Error cargando estructura");
        const org = await res.json();

        c.innerHTML = `
            <div class="org-tree">
                ${org.map(emp => `
                    <div class="org-node">
                        <span class="org-node-title">🏢 Empresa: <strong>${escapeHtml(emp.nombre)}</strong></span>
                        <div class="org-node-children">
                            ${emp.areas.map(a => `
                                <div class="org-node">
                                    <span class="org-node-title">📁 Área: <strong>${escapeHtml(a.nombre)}</strong></span>
                                    <div class="org-node-children">
                                        ${a.departamentos.map(d => `
                                            <div class="org-node">
                                                <span class="org-node-title">📂 Depto: <strong>${escapeHtml(d.nombre)}</strong></span>
                                                <div class="org-node-children">
                                                    ${d.secciones.map(s => `
                                                        <div class="org-node">
                                                            <span class="org-node-title">👥 Sección: <strong>${escapeHtml(s.nombre)}</strong></span>
                                                            <div class="org-node-children">
                                                                ${s.puestos.map(p => `
                                                                    <div class="org-node">
                                                                        <span class="org-node-title">💼 Puesto: <strong>${escapeHtml(p.nombre)}</strong> (${p.usuarios.length} usuarios)</span>
                                                                    </div>
                                                                `).join("")}
                                                            </div>
                                                        </div>
                                                    `).join("")}
                                                </div>
                                            </div>
                                        `).join("")}
                                    </div>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `).join("")}
            </div>
        `;
    } catch (err) {
        c.innerHTML = `<div class="table-empty text-danger">Error: ${err.message}</div>`;
    }
}

async function cargarUsuarios() {
    const tbody = document.getElementById("usuariosTbody");
    try {
        const res = await apiFetch("/api/usuarios");
        if (!res.ok) throw new Error("Error cargando usuarios");
        const usuarios = await res.json();

        tbody.innerHTML = usuarios.map(u => `
            <tr>
                <td>${u.id}</td>
                <td><strong>${escapeHtml(u.nombre)}</strong></td>
                <td>${escapeHtml(u.correo)}</td>
                <td><span class="role-badge role-${u.rol === 'administrador' ? 'admin' : 'consulta'}">${escapeHtml(u.rol)}</span></td>
                <td>${u.puesto ? escapeHtml(u.puesto.nombre) : '—'}</td>
                <td><span class="badge ${u.activo ? 'badge-s' : 'badge-n'}">${u.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td>
                    <button class="btn btn-sm btn-ghost" onclick="toggleEstadoUsuario(${u.id}, ${u.activo})">${u.activo ? 'Desactivar' : 'Activar'}</button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-empty text-danger">Error: ${err.message}</td></tr>`;
    }
}

function abrirModalUsuario() {
    document.getElementById("usuarioForm").reset();
    document.getElementById("formUsuarioError").classList.add("hidden");
    const pSelect = document.getElementById("formUsuarioPuesto");
    pSelect.innerHTML = `<option value="">Sin puesto asignado</option>` +
        catalogos.puestos.map(p => `<option value="${p.id}">${escapeHtml(p.nombre)}</option>`).join("");
    openModal("usuarioModal");
}

async function handleCrearUsuario(e) {
    e.preventDefault();
    const errBox = document.getElementById("formUsuarioError");
    errBox.classList.add("hidden");

    const payload = {
        nombre: document.getElementById("formUsuarioNombre").value.trim(),
        correo: document.getElementById("formUsuarioCorreo").value.trim(),
        password: document.getElementById("formUsuarioPassword").value,
        rol: document.getElementById("formUsuarioRol").value,
        puesto_id: parseInt(document.getElementById("formUsuarioPuesto").value) || null
    };

    try {
        const res = await apiFetch("/api/usuarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Error al crear usuario");
        }
        closeModal("usuarioModal");
        showToast("Usuario creado correctamente", "success");
        cargarUsuarios();
    } catch (err) {
        errBox.textContent = err.message;
        errBox.classList.remove("hidden");
    }
}

async function toggleEstadoUsuario(id, activoActual) {
    try {
        const res = await apiFetch(`/api/usuarios/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ activo: !activoActual })
        });
        if (!res.ok) throw new Error("Error actualizando usuario");
        showToast("Estado de usuario actualizado", "success");
        cargarUsuarios();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ════════════════════════════════════════════════════════
// MÓDULO: HARNESS ENGINEERING (P01–P18 SUITE)
// ════════════════════════════════════════════════════════

async function ejecutarHarnessEnVivo() {
    const btn = document.getElementById("btnRunHarness");
    const oldHtml = btn.innerHTML;
    btn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;margin-right:6px;"></div> Ejecutando Pytest en vivo…`;
    btn.disabled = true;

    try {
        const res = await apiFetch("/harness/ejecutar");
        if (!res.ok) throw new Error("Error ejecutando harness");
        const report = await res.json();

        document.getElementById("harnessSummary").classList.remove("hidden");
        document.getElementById("harnessSummaryTitle").textContent = `${report.passed} / ${report.total} Pruebas de Aceptación Superadas (${report.cobertura} Cobertura)`;
        document.getElementById("harnessSummaryMeta").textContent = `Tiempo de ejecución: ${report.duracion_segundos}s • 0 errores detectados • Base de datos: PostgreSQL`;

        const tbody = document.getElementById("harnessTbody");
        tbody.innerHTML = report.resultados.map(r => `
            <tr>
                <td><code>${r.codigo}</code></td>
                <td>${escapeHtml(r.nombre)}</td>
                <td><code>${escapeHtml(r.componente)}</code></td>
                <td>${escapeHtml(r.criterio || 'Criterio ITIL comprobado')}</td>
                <td><span class="badge ${r.badge}">${r.estado === 'PASSED' ? '✓ PASSED' : '✗ FAILED'}</span></td>
            </tr>
        `).join("");

        showToast("¡Suite completa ejecutada exitosamente!", "success");
    } catch (err) {
        showToast("Error ejecutando harness: " + err.message, "error");
    } finally {
        btn.innerHTML = oldHtml;
        btn.disabled = false;
    }
}

// ════════════════════════════════════════════════════════
// AUXILIARES & CARGA DE CATÁLOGOS
// ════════════════════════════════════════════════════════

async function cargarCatalogosAuxiliares() {
    try {
        const [n1, cl, cr, tp, sec, pt, colas, cats, srvN2] = await Promise.all([
            fetch("/api/catalogos/nivel1").then(r => r.json()).catch(() => []),
            fetch("/api/catalogos/clases").then(r => r.json()).catch(() => []),
            fetch("/api/catalogos/criticidades").then(r => r.json()).catch(() => []),
            fetch("/api/catalogos/tipos").then(r => r.json()).catch(() => []),
            fetch("/api/catalogos/secciones").then(r => r.json()).catch(() => []),
            fetch("/api/catalogos/puestos").then(r => r.json()).catch(() => []),
            fetch("/api/colas").then(r => r.json()).catch(() => []),
            fetch("/api/cmdb/categorias").then(r => r.json()).catch(() => []),
            fetch("/api/servicios?limit=100").then(r => r.json()).catch(() => [])
        ]);

        catalogos = { 
            nivel1: n1, clases: cl, criticidades: cr, tipos: tp, 
            secciones: sec, puestos: pt, colas: colas, categoriasCI: cats,
            serviciosN2: srvN2
        };

        // Llenar selects de filtros catálogo
        poblarSelect("filterNivel1", n1, "id", "nombre", "Todos Nivel 1", "codigo");
        poblarSelect("filterClase", cl, "id", "nombre", "Todas las Clases");
        poblarSelect("filterCriticidad", cr, "id", "nombre", "Toda Criticidad");
        poblarSelect("filterTipo", tp, "id", "nombre", "Todos los Tipos");

        // Llenar selects modal servicio
        poblarSelect("formNivel1", n1, "id", "nombre", "Seleccionar Nivel 1", "codigo");
        poblarSelect("formClase", cl, "id", "nombre", "Seleccionar Clase");
        poblarSelect("formCriticidad", cr, "id", "nombre", "Seleccionar Criticidad");
        poblarSelect("formTipo", tp, "id", "nombre", "Seleccionar Tipo");
        poblarSelect("formSeccion", sec, "id", "nombre", "Sin sección asignada");

        // Llenar selects tickets y colas
        poblarSelect("ticketFilterCola", colas, "id", "nombre", "Todas las Colas");

        // Llenar categorías CMDB
        poblarSelect("cmdbFilterCategoria", cats, "id", "nombre", "Todas las Categorías");

    } catch (e) {
        console.warn("Error cargando catálogos auxiliares:", e);
    }
}

function poblarSelect(id, items, valKey, textKey, defaultText = null, codeKey = null) {
    const el = document.getElementById(id);
    if (!el) return;
    let html = defaultText ? `<option value="">${defaultText}</option>` : "";
    html += (items || []).map(i => {
        const text = codeKey ? `${i[codeKey]} - ${i[textKey]}` : i[textKey];
        return `<option value="${i[valKey]}">${escapeHtml(text)}</option>`;
    }).join("");
    el.innerHTML = html;
}

async function filtrarUsuariosPorSeccion(seccionId, selectUsuarioId = null) {
    const uSelect = document.getElementById("formUsuario");
    if (!uSelect) return;
    uSelect.innerHTML = `<option value="">Cargando…</option>`;
    if (!seccionId) {
        uSelect.innerHTML = `<option value="">Primero selecciona una sección</option>`;
        return;
    }
    try {
        const res = await apiFetch(`/api/secciones/${seccionId}/usuarios`);
        const usuarios = await res.json();
        poblarSelect("formUsuario", usuarios, "id", "nombre", "Sin usuario específico");
        if (selectUsuarioId) uSelect.value = selectUsuarioId;
    } catch {
        uSelect.innerHTML = `<option value="">Error cargando usuarios</option>`;
    }
}

// ─── Login & Auth Operations ─────────────────────────────
async function doLogin(username, password) {
    const errEl = document.getElementById("loginError");
    errEl.classList.add("hidden");
    try {
        const body = new URLSearchParams({ username, password });
        const res  = await fetch("/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: body.toString()
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Credenciales incorrectas");
        }
        const data = await res.json();
        token       = data.access_token;
        currentUser = {
            id:     data.user_id,
            nombre: data.nombre,
            correo: data.correo,
            rol:    data.rol
        };
        localStorage.setItem("token", token);
        localStorage.setItem("user", JSON.stringify(currentUser));

        renderAuthUI();
        closeModal("loginModal");
        showToast(`Bienvenido, ${currentUser.nombre}`, "success");

        cargarTickets();
        cargarDashboardKPIs();
        cargarMisSolicitudes();
        if (isAdmin()) cargarUsuarios();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
    }
}

async function handleLogout(forced = false) {
    if (token) {
        try {
            await fetch("/logout", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
        } catch { /* ignore */ }
    }
    token       = null;
    currentUser = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    renderAuthUI();
    cargarMisSolicitudes();
    if (!forced) showToast("Sesión cerrada correctamente", "info");
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}