/*
 * Gráficos do Dashboard (P2, Aula 17).
 *
 * Fluxo: a view calcula os dados -> o template escreve o JSON com
 * json_script -> este arquivo lê o JSON e desenha com o Chart.js.
 * O Django continua sendo o dono dos dados; aqui só tem desenho.
 */
(function () {
    const COR_PRIMARIA = '#7a1215';
    const COR_PUBLICADO = '#1e6b34';

    function lerDados(id) {
        const elemento = document.getElementById(id);
        return elemento ? JSON.parse(elemento.textContent) : [];
    }

    // Série no tempo: matérias criadas e publicadas por mês
    const porMes = lerDados('dados-mes');
    const canvasMes = document.getElementById('grafico-mes');
    if (canvasMes && porMes.length) {
        new Chart(canvasMes, {
            type: 'bar',
            data: {
                labels: porMes.map(d => d.mes),
                datasets: [
                    { label: 'Criadas', data: porMes.map(d => d.total), backgroundColor: COR_PRIMARIA },
                    { label: 'Publicadas', data: porMes.map(d => d.publicadas), backgroundColor: COR_PUBLICADO },
                ],
            },
            options: {
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

    // Distribuição: matérias por categoria (barras horizontais)
    const porCategoria = lerDados('dados-categoria');
    const canvasCategoria = document.getElementById('grafico-categoria');
    if (canvasCategoria && porCategoria.length) {
        new Chart(canvasCategoria, {
            type: 'bar',
            data: {
                labels: porCategoria.map(d => d.categoria__nome),
                datasets: [{ label: 'Matérias', data: porCategoria.map(d => d.total), backgroundColor: COR_PRIMARIA }],
            },
            options: {
                indexAxis: 'y',
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }
})();
