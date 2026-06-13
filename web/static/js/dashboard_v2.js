// 🌌 Dashboard Eón v2.0 - Visualización en Tiempo Real
// Proyecto Eón - Arquitectura Emergente y Optimización Neuromórfica

class EonDashboard {
    constructor(wsUrl = null) {
        if (!wsUrl) {
            const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = isLocal ? window.location.host : 'api.eon.scisenselab.com';
            this.wsUrl = `${protocol}//${host}/ws`;
        } else {
            this.wsUrl = wsUrl;
        }
        
        this.nodes = new Map();
        this.egregore = null;
        this.anomalies = [];
        this.charts = {};

        // Elementos DOM
        this.networkContainer = d3.select('#network-container');
        this.egregoreMeter = d3.select('#egregore-container');
        this.metricsPanel = d3.select('#metrics-container');
        this.anomalyList = d3.select('#anomaly-list');

        // Inicializar
        this.init();
        this.connectWebSocket();
        this.startUpdates();
    }

    init() {
        // Configurar contenedores
        this.setupNetworkGraph();
        this.setupEgregoreMeter();
        this.setupMetricsPanel();
        this.setupAnomalyPanel();

        console.log('🌌 Dashboard Eón v2.0 inicializado');
    }

    setupNetworkGraph() {
        const width = this.networkContainer.node().clientWidth;
        const height = 400;

        this.svg = this.networkContainer
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('background', 'radial-gradient(circle, #1a1a2e 0%, #0a0a0f 100%)');

        // Grupo para nodos
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        // Grupo para enlaces
        this.linkGroup = this.svg.append('g').attr('class', 'links');

        // Simulación de fuerza
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));
    }

    setupEgregoreMeter() {
        const container = this.egregoreMeter;

        // Título
        container.append('h3')
            .text('🧠 Egrégor Colectivo')
            .style('color', '#e0e0e0')
            .style('margin-bottom', '20px');

        // Indicador de estado
        this.moodIndicator = container.append('div')
            .attr('class', 'mood-indicator')
            .style('width', '200px')
            .style('height', '200px')
            .style('border-radius', '50%')
            .style('border', '3px solid #9d4edd')
            .style('margin', '0 auto')
            .style('position', 'relative')
            .style('background', 'conic-gradient(from 0deg, #00ff88 0%, #ffd700 120deg, #ff4757 240deg, #00ff88 360deg)');

        // Centro del indicador
        this.moodIndicator.append('div')
            .style('width', '160px')
            .style('height', '160px')
            .style('border-radius', '50%')
            .style('background', '#0a0a0f')
            .style('position', 'absolute')
            .style('top', '20px')
            .style('left', '20px')
            .style('display', 'flex')
            .style('align-items', 'center')
            .style('justify-content', 'center')
            .style('font-size', '24px');

        // Texto de estado
        this.moodText = container.append('div')
            .style('text-align', 'center')
            .style('margin-top', '20px')
            .style('font-size', '18px')
            .style('color', '#e0e0e0');
    }

    setupMetricsPanel() {
        const container = this.metricsPanel;

        container.append('h3')
            .text('📊 Métricas de Red')
            .style('color', '#e0e0e0')
            .style('margin-bottom', '20px');

        // Contenedor de métricas
        this.metricsGrid = container.append('div')
            .attr('class', 'metrics-grid')
            .style('display', 'grid')
            .style('grid-template-columns', 'repeat(auto-fit, minmax(150px, 1fr))')
            .style('gap', '15px');

        // Métricas iniciales
        const metrics = [
            { id: 'total-nodes', label: 'Nodos Totales', value: '0', icon: '🖥️' },
            { id: 'active-nodes', label: 'Nodos Activos', value: '0', icon: '⚡' },
            { id: 'avg-error', label: 'Error Promedio', value: '0.00', icon: '📈' },
            { id: 'sync-rate', label: 'Tasa de Sync', value: '100%', icon: '🔄' },
            { id: 'anomalies', label: 'Anomalías', value: '0', icon: '⚠️' },
            { id: 'uptime', label: 'Tiempo Activo', value: '00:00:00', icon: '⏱️' }
        ];

        metrics.forEach(metric => {
            const card = this.metricsGrid.append('div')
                .attr('class', 'metric-card')
                .style('background', '#1a1a2e')
                .style('border-radius', '8px')
                .style('padding', '15px')
                .style('text-align', 'center')
                .style('border', '1px solid rgba(255,255,255,0.1)');

            card.append('div')
                .style('font-size', '24px')
                .style('margin-bottom', '5px')
                .text(metric.icon);

            card.append('div')
                .style('font-size', '14px')
                .style('color', '#888')
                .style('margin-bottom', '5px')
                .text(metric.label);

            card.append('div')
                .attr('id', metric.id)
                .style('font-size', '20px')
                .style('font-weight', 'bold')
                .style('color', '#e0e0e0')
                .text(metric.value);
        });
    }

    setupAnomalyPanel() {
        const container = this.anomalyList;

        container.append('h3')
            .text('⚠️ Anomalías Recientes')
            .style('color', '#e0e0e0')
            .style('margin-bottom', '20px');

        this.anomalyContainer = container.append('div')
            .attr('class', 'anomaly-container')
            .style('max-height', '300px')
            .style('overflow-y', 'auto');
    }

    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('🔗 Conectado al WebSocket');
                this.updateConnectionStatus(true);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (e) {
                    console.error('Error procesando mensaje WS:', e);
                }
            };

            this.ws.onclose = () => {
                console.log('🔌 Desconectado del WebSocket');
                this.updateConnectionStatus(false);
                // Reconectar en 5 segundos
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('Error WebSocket:', error);
                this.updateConnectionStatus(false);
            };

        } catch (e) {
            console.error('Error conectando WebSocket:', e);
            this.updateConnectionStatus(false);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'nodes_update':
                this.updateNodes(data.nodes);
                break;
            case 'egregore_update':
                this.updateEgregore(data.egregore);
                break;
            case 'anomaly_detected':
                this.addAnomaly(data.anomaly);
                break;
            case 'metrics_update':
                this.updateMetrics(data.metrics);
                break;
        }
    }

    updateNodes(nodes) {
        // Actualizar mapa de nodos
        this.nodes.clear();
        nodes.forEach(node => {
            this.nodes.set(node.id, node);
        });

        // Actualizar visualización
        this.updateNetworkVisualization();
    }

    updateNetworkVisualization() {
        const nodes = Array.from(this.nodes.values());
        const links = this.generateLinks(nodes);

        // Actualizar enlaces
        const link = this.linkGroup
            .selectAll('line')
            .data(links, d => `${d.source}-${d.target}`);

        link.enter()
            .append('line')
            .style('stroke', '#9d4edd')
            .style('stroke-width', 2)
            .style('stroke-opacity', 0.6)
            .merge(link);

        link.exit().remove();

        // Actualizar nodos
        const node = this.nodeGroup
            .selectAll('circle')
            .data(nodes, d => d.id);

        const nodeEnter = node.enter()
            .append('circle')
            .attr('r', 20)
            .style('fill', d => this.getNodeColor(d))
            .style('stroke', '#fff')
            .style('stroke-width', 2)
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on('drag', (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on('end', (event, d) => {
                    if (!event.active) this.simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }));

        nodeEnter.append('title')
            .text(d => `${d.name}\nEstado: ${d.status}\nMSE: ${d.error?.toFixed(4) || 'N/A'}`);

        node.merge(nodeEnter)
            .style('fill', d => this.getNodeColor(d));

        node.exit().remove();

        // Actualizar simulación
        this.simulation
            .nodes(nodes)
            .on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
            });

        this.simulation.force('link').links(links);
        this.simulation.alpha(1).restart();
    }

    generateLinks(nodes) {
        // Generar enlaces basados en conexiones MQTT o proximidad
        const links = [];
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                if (Math.random() < 0.3) { // 30% de probabilidad de conexión
                    links.push({
                        source: nodes[i].id,
                        target: nodes[j].id
                    });
                }
            }
        }
        return links;
    }

    getNodeColor(node) {
        switch (node.status) {
            case 'active': return '#00ff88';
            case 'learning': return '#ffd700';
            case 'error': return '#ff4757';
            case 'idle': return '#888';
            default: return '#9d4edd';
        }
    }

    updateEgregore(egregore) {
        this.egregore = egregore;

        if (!egregore) return;

        // Actualizar indicador de estado
        const moodColors = {
            'agitated': '#ff4757',
            'meditative': '#00d9ff',
            'awakening': '#ffd700',
            'balanced': '#00ff88'
        };

        const color = moodColors[egregore.mood] || '#9d4edd';
        const intensity = egregore.intensity || 0.5;

        this.moodIndicator
            .style('box-shadow', `0 0 ${intensity * 50}px ${color}`);

        // Actualizar texto
        this.moodText
            .text(`${egregore.mood.toUpperCase()} (${(intensity * 100).toFixed(0)}%)`);
    }

    updateMetrics(metrics) {
        // Actualizar métricas en el DOM
        Object.entries(metrics).forEach(([key, value]) => {
            const element = d3.select(`#${key.replace('_', '-')}`);
            if (!element.empty()) {
                element.text(this.formatMetricValue(key, value));
            }
        });
    }

    formatMetricValue(key, value) {
        switch (key) {
            case 'avg_error':
                return value.toFixed(4);
            case 'sync_rate':
                return `${(value * 100).toFixed(1)}%`;
            case 'uptime':
                return this.formatUptime(value);
            default:
                return value.toString();
        }
    }

    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    addAnomaly(anomaly) {
        this.anomalies.unshift(anomaly);
        this.anomalies = this.anomalies.slice(0, 10); // Mantener últimas 10

        this.updateAnomalyList();
    }

    updateAnomalyList() {
        const container = this.anomalyContainer;

        // Limpiar
        container.selectAll('.anomaly-item').remove();

        // Añadir anomalías
        const items = container.selectAll('.anomaly-item')
            .data(this.anomalies)
            .enter()
            .append('div')
            .attr('class', 'anomaly-item')
            .style('background', '#1a1a2e')
            .style('border-radius', '6px')
            .style('padding', '10px')
            .style('margin-bottom', '8px')
            .style('border-left', d => `4px solid ${this.getSeverityColor(d.severity)}`);

        items.append('div')
            .style('font-size', '12px')
            .style('color', '#888')
            .text(d => new Date(d.timestamp * 1000).toLocaleTimeString());

        items.append('div')
            .style('font-size', '14px')
            .style('color', '#e0e0e0')
            .style('margin', '5px 0')
            .text(d => d.description);

        items.append('div')
            .style('font-size', '12px')
            .style('color', '#ffd700')
            .text(d => `Z-score: ${d.z_score.toFixed(2)}`);
    }

    getSeverityColor(severity) {
        switch (severity) {
            case 'critical': return '#ff4757';
            case 'anomaly': return '#ff6b35';
            case 'warning': return '#ffd700';
            default: return '#888';
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = d3.select('#connection-status');
        if (!statusElement.empty()) {
            statusElement
                .style('color', connected ? '#00ff88' : '#ff4757')
                .text(connected ? '🟢 Conectado' : '🔴 Desconectado');
        }
    }

    startUpdates() {
        // Actualizar métricas cada 5 segundos
        setInterval(() => {
            this.fetchMetrics();
        }, 5000);

        // Actualizar uptime
        setInterval(() => {
            const uptimeElement = d3.select('#uptime');
            if (!uptimeElement.empty()) {
                const current = parseInt(uptimeElement.text().split(':').reduce((acc, val, idx) => {
                    return acc + parseInt(val) * Math.pow(60, 2 - idx);
                }, 0)) + 1;
                uptimeElement.text(this.formatUptime(current));
            }
        }, 1000);
    }

    async fetchMetrics() {
        try {
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();

            if (data.success) {
                this.updateMetrics(data.metrics);
            }
        } catch (e) {
            console.error('Error fetching metrics:', e);
        }
    }
}

// Inicializar dashboard cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Verificar si estamos en la página del dashboard
    if (document.getElementById('network-container')) {
        const dashboard = new EonDashboard();
        window.eonDashboard = dashboard;
    }
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EonDashboard;
}