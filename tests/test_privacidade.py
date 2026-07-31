from resume_v4.services.privacidade import ServicoPrivacidade

def test_remove_email_e_telefone():
    texto='João da Silva\njoao@example.com\n(83) 99999-0000'
    resultado=ServicoPrivacidade().anonimizar(texto)
    assert 'joao@example.com' not in resultado['texto']
    assert '99999-0000' not in resultado['texto']
