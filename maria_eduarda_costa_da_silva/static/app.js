// Urna Eletrônica - telas da versão web.
// Todas as regras e o banco ficam no Python (app.py); aqui só mostramos e enviamos dados.

const MINIMO = Number(document.body.dataset.minimo);
const CORES = ["#2f6fd1", "#e0533d", "#2e9e48", "#9b59b6", "#f1a321", "#16a2b8"];
const $ = (id) => document.getElementById(id);

// ------------------------------------------------------------ utilidades
async function api(metodo, url, dados) {
  const resposta = await fetch(url, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: dados ? JSON.stringify(dados) : undefined,
  });
  const json = await resposta.json();
  if (!resposta.ok) throw new Error(json.erro || "Erro inesperado.");
  return json;
}

let timerAviso;
function aviso(texto, tipo = "ok") {
  const caixa = $("aviso");
  caixa.textContent = texto;
  caixa.className = `aviso ${tipo} mostrar`;
  clearTimeout(timerAviso);
  timerAviso = setTimeout(() => caixa.classList.remove("mostrar"), 3200);
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

const doisDigitos = (n) => String(n).padStart(2, "0");

function bip() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    osc.frequency.value = 1200;
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch (e) { /* navegador sem áudio */ }
}

// ------------------------------------------------------------ abas
document.querySelectorAll(".aba").forEach((botao) =>
  botao.addEventListener("click", () => abrirAba(botao.dataset.aba)));

function abrirAba(nome) {
  document.querySelectorAll(".aba").forEach((b) => b.classList.toggle("ativa", b.dataset.aba === nome));
  document.querySelectorAll(".painel").forEach((p) => p.classList.toggle("ativo", p.id === nome));
  atualizarTudo();
}

async function atualizarTudo() {
  try {
    await Promise.all([carregarCandidatos(), carregarEleitores(), carregarApuracao(), carregarStatus()]);
  } catch (e) {
    aviso("Não foi possível falar com o servidor. O app.py está rodando?", "erro");
  }
}

// ============================================================ VOTAÇÃO
const urna = { eleitor: null, digitos: "", branco: false, travada: false };
let candidatos = [];

function desenharVisor(fim = false) {
  const visor = $("visor");

  if (fim) {
    visor.innerHTML = `<div class="centro fim">FIM</div>`;
    return;
  }
  if (!urna.eleitor) {
    visor.innerHTML = `
      <div class="centro">
        <div class="bloqueada">URNA BLOQUEADA</div>
        <div class="aguardando">Aguardando o mesário liberar o próximo eleitor</div>
      </div>`;
    return;
  }

  const caixas = [0, 1].map((i) => {
    const atual = i === urna.digitos.length && !urna.branco ? " atual" : "";
    return `<div class="digito${atual}">${urna.digitos[i] || ""}</div>`;
  }).join("");

  let info = "";
  if (urna.branco) {
    info = `<div class="grande branco-msg">VOTO EM BRANCO</div>`;
  } else if (urna.digitos.length === 2) {
    const c = candidatos.find((x) => x.numero === Number(urna.digitos));
    info = c
      ? `Nome: <strong>${escapar(c.nome)}</strong><br>Partido: <strong>${escapar(c.partido)}</strong>`
      : `<div class="nulo"><strong>NÚMERO ERRADO</strong></div><div class="grande nulo">VOTO NULO</div>`;
  }

  const prontoParaConfirmar = urna.branco || urna.digitos.length === 2;
  visor.innerHTML = `
    <div class="cargo-topo">SEU VOTO PARA</div>
    <div class="cargo">PREFEITO</div>
    <div class="linha-numero">Número: ${caixas}</div>
    <div class="info">${info}</div>
    ${prontoParaConfirmar ? `
      <div class="rodape">
        Aperte a tecla:<br>
        &nbsp;&nbsp;<span class="c">CONFIRMA</span> para CONFIRMAR este voto<br>
        &nbsp;&nbsp;<span class="r">CORRIGE</span> para REINICIAR este voto
      </div>` : ""}
    <div class="eleitor">Eleitor(a): ${escapar(urna.eleitor.nome)}</div>`;
}

function statusMesario(texto, tipo = "ok") {
  const p = $("status-mesario");
  p.textContent = texto;
  p.className = `status ${tipo}`;
}

$("form-liberar").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (urna.eleitor) return;
  const titulo = $("titulo-voto").value.trim();
  if (!titulo) return statusMesario("Digite o título do eleitor.", "erro");
  try {
    await carregarCandidatos();
    urna.eleitor = await api("POST", "/api/liberar", { titulo });
    urna.digitos = "";
    urna.branco = false;
    $("titulo-voto").disabled = true;
    $("btn-liberar").disabled = true;
    $("btn-cancelar").disabled = false;
    statusMesario(`Urna liberada para ${urna.eleitor.nome}.`);
    document.activeElement.blur();
    desenharVisor();
  } catch (erro) {
    statusMesario(erro.message, "erro");
  }
});

$("btn-cancelar").addEventListener("click", () => {
  statusMesario("Eleitor cancelado (nenhum voto registrado).");
  bloquearUrna();
});

function bloquearUrna() {
  Object.assign(urna, { eleitor: null, digitos: "", branco: false, travada: false });
  $("titulo-voto").disabled = false;
  $("titulo-voto").value = "";
  $("btn-liberar").disabled = false;
  $("btn-cancelar").disabled = true;
  $("titulo-voto").focus();
  desenharVisor();
}

function podeDigitar() {
  return urna.eleitor && !urna.travada;
}

function digitar(n) {
  if (!podeDigitar() || urna.branco || urna.digitos.length >= 2) return;
  urna.digitos += n;
  desenharVisor();
}

function votarBranco() {
  if (!podeDigitar()) return;
  if (urna.digitos) return aviso("Para votar em branco, aperte CORRIGE antes.", "erro");
  urna.branco = true;
  desenharVisor();
}

function corrigir() {
  if (!podeDigitar()) return;
  urna.digitos = "";
  urna.branco = false;
  desenharVisor();
}

async function confirmar() {
  if (!podeDigitar()) return;
  let voto;
  if (urna.branco) voto = "BRANCO";
  else if (urna.digitos.length === 2) voto = urna.digitos;
  else return;

  urna.travada = true;
  const nome = urna.eleitor.nome;
  try {
    await api("POST", "/api/votar", { titulo: urna.eleitor.titulo, voto });
    bip();
    desenharVisor(true);
    statusMesario(`Voto de ${nome} registrado com sucesso.`);
    carregarStatus();
    setTimeout(bloquearUrna, 1500);
  } catch (erro) {
    statusMesario(erro.message, "erro");
    bloquearUrna();
  }
}

document.querySelectorAll(".tecla").forEach((t) =>
  t.addEventListener("click", () => digitar(t.dataset.num)));
$("btn-branco").addEventListener("click", votarBranco);
$("btn-corrige").addEventListener("click", corrigir);
$("btn-confirma").addEventListener("click", confirmar);

// Votar pelo teclado do computador
document.addEventListener("keydown", (e) => {
  if (!$("votacao").classList.contains("ativo") || !podeDigitar()) return;
  if (/^[0-9]$/.test(e.key)) digitar(e.key);
  else if (e.key.toUpperCase() === "B") votarBranco();
  else if (e.key === "Backspace") { e.preventDefault(); corrigir(); }
  else if (e.key === "Enter") { e.preventDefault(); confirmar(); }
});

async function carregarStatus() {
  const s = await api("GET", "/api/status");
  $("contador-votos").textContent = `Votos na urna: ${s.total} (mínimo ${s.minimo})`;
  $("contador-aptos").textContent = `Eleitores que ainda não votaram: ${s.aptos}`;
  $("barra-progresso").style.width = `${Math.min(s.total / s.minimo, 1) * 100}%`;
}

// ============================================================ CANDIDATOS
let candidatoEditando = null;

async function carregarCandidatos() {
  candidatos = await api("GET", "/api/candidatos");
  $("lista-candidatos").innerHTML = candidatos.map((c) => `
    <tr data-numero="${c.numero}" class="${c.numero === candidatoEditando ? "selecionada" : ""}">
      <td><strong>${doisDigitos(c.numero)}</strong></td>
      <td>${escapar(c.nome)}</td>
      <td>${escapar(c.partido)}</td>
    </tr>`).join("");
  $("vazio-candidatos").style.display = candidatos.length ? "none" : "block";
}

$("lista-candidatos").addEventListener("click", (e) => {
  const linha = e.target.closest("tr");
  if (!linha) return;
  const c = candidatos.find((x) => x.numero === Number(linha.dataset.numero));
  candidatoEditando = c.numero;
  $("cand-numero").value = doisDigitos(c.numero);
  $("cand-numero").disabled = true;
  $("cand-nome").value = c.nome;
  $("cand-partido").value = c.partido;
  $("titulo-form-candidato").textContent = `Alterar candidato ${doisDigitos(c.numero)}`;
  $("btn-salvar-candidato").textContent = "Salvar alterações";
  $("btn-excluir-candidato").hidden = false;
  carregarCandidatos();
});

function limparCandidato() {
  candidatoEditando = null;
  $("form-candidato").reset();
  $("cand-numero").disabled = false;
  $("titulo-form-candidato").textContent = "Novo candidato";
  $("btn-salvar-candidato").textContent = "Cadastrar";
  $("btn-excluir-candidato").hidden = true;
  carregarCandidatos();
}

$("form-candidato").addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = { nome: $("cand-nome").value, partido: $("cand-partido").value };
  try {
    const r = candidatoEditando === null
      ? await api("POST", "/api/candidatos", { ...dados, numero: $("cand-numero").value })
      : await api("PUT", `/api/candidatos/${candidatoEditando}`, dados);
    aviso(r.mensagem);
    limparCandidato();
    $("cand-numero").focus();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

$("btn-excluir-candidato").addEventListener("click", async () => {
  if (!confirm(`Excluir o candidato ${doisDigitos(candidatoEditando)}?`)) return;
  try {
    aviso((await api("DELETE", `/api/candidatos/${candidatoEditando}`)).mensagem);
    limparCandidato();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

$("btn-limpar-candidato").addEventListener("click", limparCandidato);

// ============================================================ ELEITORES
let eleitores = [];
let eleitorEditando = null;

async function carregarEleitores() {
  eleitores = await api("GET", "/api/eleitores");
  $("lista-eleitores").innerHTML = eleitores.map((el) => `
    <tr data-titulo="${escapar(el.titulo)}" class="${el.titulo === eleitorEditando ? "selecionada" : ""}">
      <td>${escapar(el.titulo)}</td>
      <td>${escapar(el.nome)}</td>
      <td>${el.ja_votou
        ? '<span class="etiqueta votou">✔ Já votou</span>'
        : '<span class="etiqueta apto">Apto</span>'}</td>
    </tr>`).join("");
  $("vazio-eleitores").style.display = eleitores.length ? "none" : "block";
}

$("lista-eleitores").addEventListener("click", (e) => {
  const linha = e.target.closest("tr");
  if (!linha) return;
  const el = eleitores.find((x) => x.titulo === linha.dataset.titulo);
  eleitorEditando = el.titulo;
  $("ele-titulo").value = el.titulo;
  $("ele-titulo").disabled = true;
  $("ele-nome").value = el.nome;
  $("titulo-form-eleitor").textContent = `Alterar eleitor ${el.titulo}`;
  $("btn-salvar-eleitor").textContent = "Salvar alterações";
  $("btn-excluir-eleitor").hidden = false;
  carregarEleitores();
});

function limparEleitor() {
  eleitorEditando = null;
  $("form-eleitor").reset();
  $("ele-titulo").disabled = false;
  $("titulo-form-eleitor").textContent = "Novo eleitor";
  $("btn-salvar-eleitor").textContent = "Cadastrar";
  $("btn-excluir-eleitor").hidden = true;
  carregarEleitores();
}

$("form-eleitor").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const r = eleitorEditando === null
      ? await api("POST", "/api/eleitores", { titulo: $("ele-titulo").value, nome: $("ele-nome").value })
      : await api("PUT", `/api/eleitores/${encodeURIComponent(eleitorEditando)}`, { nome: $("ele-nome").value });
    aviso(r.mensagem);
    limparEleitor();
    $("ele-titulo").focus();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

$("btn-excluir-eleitor").addEventListener("click", async () => {
  if (!confirm(`Excluir o eleitor ${eleitorEditando}?`)) return;
  try {
    aviso((await api("DELETE", `/api/eleitores/${encodeURIComponent(eleitorEditando)}`)).mensagem);
    limparEleitor();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

$("btn-limpar-eleitor").addEventListener("click", limparEleitor);

// ============================================================ APURAÇÃO
async function carregarApuracao() {
  const r = await api("GET", "/api/apuracao");

  const caixa = (valor, rotulo) => `<div class="numero-resumo"><strong>${valor}</strong><span>${rotulo}</span></div>`;
  $("resumo").innerHTML = caixa(r.total, "Total de votos") + caixa(r.validos, "Válidos")
    + caixa(r.brancos, "Brancos") + caixa(r.nulos, "Nulos");

  const situacao = $("situacao");
  if (!r.liberada) {
    $("grafico").innerHTML = `<div class="aguardando-apuracao">Aguardando o mínimo de votos...</div>`;
    situacao.textContent = `A apuração é liberada depois de ${r.minimo} votos (faltam ${r.minimo - r.total}).`;
    situacao.className = "situacao cinza";
    return;
  }

  $("grafico").innerHTML = r.candidatos.map((c, i) => {
    const perc = r.validos ? (c.votos / r.validos) * 100 : 0;
    return `
      <div class="linha-candidato">
        <div><div class="nome">${doisDigitos(c.numero)} · ${escapar(c.nome)}</div>
             <div class="partido">${escapar(c.partido)}</div></div>
        <div class="trilho">
          <div class="preenchimento" style="width:${perc}%; background:${CORES[i % CORES.length]}"></div>
          <div class="marca-50"></div>
        </div>
        <div>${c.votos} votos (${perc.toFixed(1)}%)</div>
      </div>`;
  }).join("") + `<div class="legenda-50">┆ 50% dos votos válidos (maioria absoluta)</div>`;

  situacao.textContent = r.situacao;
  situacao.className = r.situacao.startsWith("ELEITO") ? "situacao eleito" : "situacao";
}

$("btn-exemplo").addEventListener("click", async () => {
  try {
    aviso((await api("POST", "/api/exemplo")).mensagem);
    atualizarTudo();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

$("btn-zerar").addEventListener("click", async () => {
  if (!confirm("Apagar todos os votos e liberar os eleitores para votar de novo?")) return;
  try {
    aviso((await api("POST", "/api/zerar")).mensagem);
    atualizarTudo();
  } catch (erro) {
    aviso(erro.message, "erro");
  }
});

// ------------------------------------------------------------ início
desenharVisor();
atualizarTudo();
