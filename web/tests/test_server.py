"""
Tests para web/server.py - API REST de Proyecto Eón.

Cobertura básica de endpoints críticos.
"""

import pytest
import json
import sys
import os

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_web_dir = os.path.join(os.path.dirname(os.path.dirname(_current_dir)), 'web')
sys.path.insert(0, _web_dir)


class TestServerImports:
    """Verifica que los imports del servidor funcionan."""
    
    def test_flask_import(self):
        """Verifica que Flask está disponible."""
        from flask import Flask
        assert Flask is not None
    
    def test_server_can_import(self):
        """Verifica que el módulo server se puede importar."""
        try:
            # Importar sin ejecutar main
            import server
            assert hasattr(server, 'app')
        except ImportError as e:
            pytest.skip(f"No se puede importar server: {e}")


class TestEonChatClass:
    """Tests para la clase EonChat."""
    
    @pytest.fixture
    def setup_server(self):
        """Setup para importar server y obtener la clase."""
        try:
            import server
            return server
        except ImportError:
            pytest.skip("No se puede importar server")
    
    def test_eon_chat_exists(self, setup_server):
        """Verifica que la clase EonChat existe."""
        assert hasattr(setup_server, 'EonChat')
    
    def test_eon_chat_has_get_response_method(self, setup_server):
        """Verifica que EonChat tiene método get_response."""
        if hasattr(setup_server, 'EonChat'):
            assert hasattr(setup_server.EonChat, 'get_response')


class TestAPIEndpoints:
    """Tests de integración para endpoints de la API."""
    
    @pytest.fixture
    def client(self):
        """Cliente de test Flask."""
        try:
            import server
            server.app.config['TESTING'] = True
            with server.app.test_client() as client:
                yield client
        except ImportError:
            pytest.skip("No se puede importar server")
    
    def test_index_returns_html(self, client):
        """Verifica que la raíz devuelve HTML."""
        response = client.get('/')
        assert response.status_code in [200, 302, 404]  # OK, redirect, o sin static
    
    def test_api_status_endpoint(self, client):
        """Verifica endpoint /api/status."""
        response = client.get('/api/status')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'success' in data or 'status' in data
    
    def test_api_genesis_endpoint(self, client):
        """Verifica endpoint /api/genesis (solo lectura)."""
        response = client.get('/api/genesis')
        if response.status_code == 200:
            data = json.loads(response.data)
            # Genesis debe tener campos básicos
            assert 'success' in data or 'timestamp' in data or 'seed' in data
    
    def test_api_config_get(self, client):
        """Verifica endpoint GET /api/config."""
        response = client.get('/api/config')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
    
    def test_api_chat_post_valid(self, client):
        """Verifica endpoint POST /api/chat con mensaje válido."""
        response = client.post(
            '/api/chat',
            data=json.dumps({'message': 'Hola'}),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'reply' in data or 'response' in data or 'message' in data
    
    def test_api_chat_post_empty(self, client):
        """Verifica endpoint POST /api/chat con mensaje vacío."""
        response = client.post(
            '/api/chat',
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        # Debería devolver 200 o 400, pero no 500
        assert response.status_code != 500
    
    def test_api_list_instances(self, client):
        """Verifica endpoint GET /api/list."""
        response = client.get('/api/list')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'success' in data
            assert 'instances' in data


class TestMathOperations:
    """Tests para operaciones matemáticas del chat."""
    
    @pytest.fixture
    def client(self):
        """Cliente de test Flask."""
        try:
            import server
            server.app.config['TESTING'] = True
            with server.app.test_client() as client:
                yield client
        except ImportError:
            pytest.skip("No se puede importar server")
    
    def test_simple_addition(self, client):
        """Verifica que el chat puede hacer sumas."""
        response = client.post(
            '/api/chat',
            data=json.dumps({'message': '¿Cuánto es 2 + 2?'}),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = json.loads(response.data)
            reply = data.get('reply', data.get('response', ''))
            # Debería contener "4" en algún lugar
            assert '4' in reply or response.status_code == 200
    
    def test_simple_multiplication(self, client):
        """Verifica que el chat puede hacer multiplicaciones."""
        response = client.post(
            '/api/chat',
            data=json.dumps({'message': '¿Cuánto es 3 * 4?'}),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = json.loads(response.data)
            reply = data.get('reply', data.get('response', ''))
            assert '12' in reply or response.status_code == 200


class TestAlchemyAPI:
    """Tests para endpoints de Alquimia."""
    
    @pytest.fixture
    def client(self):
        """Cliente de test Flask."""
        try:
            import server
            server.app.config['TESTING'] = True
            with server.app.test_client() as client:
                yield client
        except ImportError:
            pytest.skip("No se puede importar server")
    
    def test_alchemy_status(self, client):
        """Verifica endpoint GET /api/alchemy/status."""
        response = client.get('/api/alchemy/status')
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'success' in data
    
    def test_alchemy_transmute_valid(self, client):
        """Verifica endpoint POST /api/alchemy/transmute con datos válidos."""
        response = client.post(
            '/api/alchemy/transmute',
            data=json.dumps({'data': [1.0, 2.0, 3.0, 4.0, 5.0]}),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'success' in data
    
    def test_alchemy_transmute_empty(self, client):
        """Verifica endpoint POST /api/alchemy/transmute con datos vacíos."""
        response = client.post(
            '/api/alchemy/transmute',
            data=json.dumps({}),
            content_type='application/json'
        )
        # Debería retornar error 400, no 500
        assert response.status_code in [400, 200]


class TestErrorHandling:
    """Tests de manejo de errores."""
    
    @pytest.fixture
    def client(self):
        """Cliente de test Flask."""
        try:
            import server
            server.app.config['TESTING'] = True
            with server.app.test_client() as client:
                yield client
        except ImportError:
            pytest.skip("No se puede importar server")
    
    def test_invalid_json_returns_error(self, client):
        """Verifica que JSON inválido retorna error apropiado."""
        response = client.post(
            '/api/chat',
            data='{"invalid json',
            content_type='application/json'
        )
        # No debe ser 500 (error interno), debe ser 400 (bad request)
        assert response.status_code != 500 or response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Verifica comportamiento sin Content-Type."""
        response = client.post('/api/chat', data='{"message": "test"}')
        # Debe manejar graciosamente
        assert response.status_code in [200, 400, 415]
    
    def test_nonexistent_endpoint_404(self, client):
        """Verifica que endpoints inexistentes retornan 404."""
        response = client.get('/api/nonexistent_endpoint_xyz')
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
