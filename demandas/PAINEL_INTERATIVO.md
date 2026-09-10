# 🎛️ Painel Interativo de Demandas

Este arquivo espelha o conteúdo do CSV de forma interativa. Marque com um `[x]` a demanda que deseja que a Inteligência Artificial inicie. Você também pode preencher o campo `💡 Solução Sugerida` se quiser direcionar o agente para uma implementação específica.

## 🔴 Prioridade ALTA

- [ ] **ID 1**: Não exclui usuário (Módulo: Usuários)
  - **Descrição:** Ao clicar no botão Remover Conta, o usuário não é excluído.  CONTINUA NÃO EXCLUINDO O USUÁRIO.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 2**: Criar token da conta para criação de instâncias. (Módulo: Meu Perfil)
  - **Descrição:** Além do username, seria recomendado exibir o token da conta para autenticação a criação de uma nova instância.  DE FATO O TOKEN DA CONTA FOI IMPLEMENTADO E JÁ ESTÁ FUNCIONANDO NA CRIAÇÃO DE NOVA INSTANCIA. PORÉM DEVERIA INFROMAR ISSO DA DOCUMENTAÇÃO. ALGUNS USUÁRIO ACREDITAM QUE TEM QUE INFORMAR TOKEN DE UMA INSTANCIA EXISTENTE.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 3**: Autonomia para exclusão da conta (Módulo: Meu Perfil)
  - **Descrição:** Permitir que o usuário exclua a conta caso não queira mais usar a plataforma da Uzapi.  OBS: AO EXCLUIR A CONTA, DEVE-SE TAMBÉM EXCLUIR A ASSIANTURA DESSECLIENTE NO ASAAS. CASO ELE VOLTE A FAZER UM NOVO CADASTRO NA UZAPI E CONTRATAR UMA NOVA INSTANCIA PAGA, A PLAATFORMA PODE REAPROVEITAR O CADASTRO DO ASAAS E SÓ CRIAR A NOVA ASSIANTURA.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 4**: Acrescentar coluna e filtro de cupom e data ultimo pagamento (Módulo: Assinaturas)
  - **Descrição:** É de extrema utilidade acrescentar coluna e filtro de cupom e datado ultimo pagamento para cada assiantura. Pois isso vai pemitir sabermos quantas assianturas o parceiro conseguiu no mês com os indicados que usaram seu cupom exclusivo. 
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 6**: Solicitar CEP e Numero do Imóvel na contratação de instancias (Módulo: Contratar Instâncias)
  - **Descrição:** Ao contratar instancias pagas pela primeira vez, além do CPF/CNPJ, deve solicitar o CEP e número do imóvel para o preenchimento automático de endereço na assiantura do cliente no Asaas. Isso é necessário para emissão da NF.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 45**: Aceitar apenas numeros de celular do Brasil (+55) no cadastro (Módulo: Cadastro)
  - **Descrição:** Como estamos usando gateway de pagamento do Asaas, não será possível por enquanto atender clientes estrangeiros na plataforma. Portanto, remover a opção de escolher o DDI  do país ao informa ro numero de celular para receber o código de ativação da conta (OTP)
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 48**: Botão Criar Instancia Ativo para Assinaturas Vencidas (Módulo: Instâncias)
  - **Descrição:** Assim que assiantura do usuário chega no vencimento, o botão Criar instância continua ativo. O certo é desativar quando a assiantura está com o status vencido ou pendente.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 51**: Botão atualizar instancia não funciona (Módulo: Instâncias)
  - **Descrição:** Ao clicar em atualizar instancia, a mesma não atualiza para a ultima versão disponibilizada, sendo necessária ter que excluir e cria ruma nova instancia para vir com a nova versão.  TESTAMOS E ATUALIZOU PERFEITAMNETE A VERSÃO DA INSTANCIA SEM PRECISAR RECRIÁ-LA.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 54**: INTEGRAÇÃO COM O CHATWOOT COM VERSÕES MAIS ATUAIS (Módulo: API)
  - **Descrição:** Dá erro ao criar inbox. Sò está funcionando com a versão 4.1.0  TESTEAMOS NA VERSÃO LATEST (4.16.2) E FUNCIONOU PERFEITAMENTE
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 55**: Proxy de IPS do Brasil (Módulo: API)
  - **Descrição:** Geralmnete quando o usuário se conecta na Uzapi, o WhatsApp exibe um alerta dizendo que ela está se conectando em um dispositivo de Ashburn (EUA). Talvez isso tem levantado um Red Flag e contribuindo para possíveis banimentos de certos clientes. Seria interessante se usássemos apenas IP do Brasil em noss o Proxy. Existe um serviço chamado Proxy Seller que dispões IPs do Brasil por um prezo acessível.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 56**: URL dos tickets no formato errado (Módulo: Suporte)
  - **Descrição:** Sempre que um ticket pe aberto/atualizado éenviado a URL para o email / whatsapp. Porém a URL base está sendo uzapi.com.br, e não painel.uzapi.com.br. Isso etsá fazendo que o usuário seja direcionado para uma página inexistente (erro 404)  TESTAMOS ESTÁ EXIBINDO A URL CORRETA.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 63**: Não exibe QRCode para instancias com status Pausada (Módulo: Instâncias)
  - **Descrição:** Sempre que uma instancia tem o status alterado para Pausada, ela passa a não exibir mais o QRCode para uma nova autenticação, sendo necessário excluí-la e criar uma nova.  OBS: CONSEGUI CONTORNAR O PROBLEMA, CLICANDO EM REINIIAR INSTANCIA, ONDE O STATUS SAIU DE PAUSADA PARA DESCONECTADA. VOLTANDO ENTÃO A EXIBIR O QRCODE.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 67**: Exclusões de mensagens para todos também parou de funcionar (Módulo: API)
  - **Descrição:** Ao apagar a mensagem enviada, ela entra na fila e é descartada
  - 💡 **Solução Sugerida pelo Dev:** 

## 🟢 Prioridade BAIXA

- [ ] **ID 10**: Tela de parceiros (Módulo: Outro)
  - **Descrição:** Embora não seja tão importante para agora, seria interessante uma tela , ond eo admin poderia verificar os usuários com perfil de parceiros e vê as quantidade de pessoas que criaram conta através do cupom dele e o total de venda/comissão que ele já fez na Uzapi.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 11**: Tela de comissões (Módulo: Outro)
  - **Descrição:** Também seri interessnate uma tela exclusiva para usuários com o perfil Parceiro, para eles acompanharem o progresso deles nas vendas. Saber quanto faturaram de um determinado mês. Mostrar o saldo que eles tem para saque, o valor que já sacaram e uma opção para solicitar novo saque (onde ele poderia cadastrar uma chave PIX. Se for parceiro fora do Brasil, poderia informar o email do PayPal ou Stripe)
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 12**: Tela de saques (Módulo: Outro)
  - **Descrição:** Uma tela onde os admin poderia ver a lista de solicitações de saque, onde cada solicitação de saque teria botão de aprovar ou recusar. Em caso de recursa, o valor pendente de saque (na visão do parceiro) voltaria para o saldo a ser sacado. Já em caso de aprovação (apõs o admin fazer o pix para o parceiro), o valor seria debitado do saldo atual do parceiro e somando ao total de saque realizado.
  - 💡 **Solução Sugerida pelo Dev:** 

## 🟢 Prioridade NORMAL

- [ ] **ID 13**: Não revoga as instância do usuário (Módulo: Usuários)
  - **Descrição:** Ao clicar no botão revogar instancias, exibe uma notificação que as instancias foram revogadas e desloga o usuário. Ao realizar novamnete o login e acessar o menu Instancias, as instancias continuam lá.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 14**: Não localiza usuário por e-mail (Módulo: Usuários)
  - **Descrição:** Ao pesquisar pelo e-mail de um usuário existente, ele não aparece na pesquisa
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 15**: Não localiza assinante por e-mail (Módulo: Assinaturas)
  - **Descrição:** Ao pesquisar pelo e-mail de um assinante existente, ele não aparece na pesquisa
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 16**: Exibe vencimento errado (Módulo: Assinaturas)
  - **Descrição:** Ao informar uma nova data de vencimentio para a assinatura, a mesma não é exibida corretamnete para o usuário. A data exibida é proveniente desse cálculo: Data Vencimento Informada - Dias de Tolerância - 1 dia. O Adequado é o usuário ver a mesma data de vencimento que o admin informou na edição da assinatura. O INTUITO DA LOGICA É JUSTAMENTE ESSE , O USUARIO NAO PODE VER NEM SEQUER SABER QUE EXISTE ESSE PRAZO DE TOLERANCIA, NAO PODEMOS APRESENTAR PARA O USUARIO A DATA DE VENCIMENTO CONSIDERANDO OS DIAS DE TOLERANCIA. SAO DOIS CONCEITOS DIFERENTES DATA DE VENCIMENTO E DATA DE CORTE.  DE FATO, NÃO É PARA MOSTRAR A DATA DE CORTE PARA O USUÁRIO. A QUESTÃO É QUE QUANDO O ADMIN COLOCA A DATA DE VENCIMENTO, ELE É OBRIGADO A CONSIDERAR + 8 DIAS NA DATA DE VENCIMENTO A SER INSERIDA PARA QUE EXIBA A DATA DE VENCIMENTO CORRETA PARA O USUÁRIO. O OBJETIVO DA CORREÇÃO DESSE BUG É FAZER COM QUE O ADMIN COLOQUE DE FATO A DATA DE VENCIMENTO E A DATA DE CORTE SEJA AUTOMATICAMNETE ATRIBUIDA A DATA DE VENCIMENTO FINAL. OU ENTÃO, NÃO FAZER ESSA ATRIBUIÇÃO AUTOMATICA, SIMPLESMNETE EXIBIR AO USUÁRIO A MESMA DATA DE VENCIMENTO QUE O ADMIN COLOCOU E A DATA DE CORTE SER REALIZADA NORMALMNETE. SEM QUE O USUÁRIO SAIBA.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 17**: Erro na contagem de instancias criadas (Módulo: Contratar Instâncias)
  - **Descrição:** A maioria das assinaturas não exibe a quantidade de instancias criadas do assinante. Ex: Se o usuário contratou 3 instancias e tem 2 criadas, exibe assim: 0/3 ao invés de 2/3
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 18**: Definir preço máximo no uso do cupom (Módulo: Cupons)
  - **Descrição:** Seria bom definir um valor máximo de contratação para o uso do cupom. Isso evitaria o usuário ter a sensação de desconto vitalício conforme for contratando mais instancias.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 19**: Botão para exportar lista de assinaturas (Módulo: Assinaturas)
  - **Descrição:** Na tela de assinaturas, é importante ter um botão para exportar a lista filtrada de assianturas no formato .csv
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 20**: Scroll Down automático (Módulo: Suporte)
  - **Descrição:** Após alguns segundo na tela de suporte, ocorre um scroll down automático, focando no final da tela. Isso prejudica muito o usuário no momento que está escrevendo ou respondendo o ticket.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 21**: Verificar se o numero é valido (Módulo: API)
  - **Descrição:** Adicionar um endpoint capaz de verificar se o numero é valido para Whatsapps
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 22**: Não tem o filtro Trial Expirado (Módulo: Assinaturas)
  - **Descrição:** Não é possível filtrar a lista de assinantes pelo status Trial Expirado
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 24**: Modal de criar instancia está cortado (Módulo: Instâncias)
  - **Descrição:** No modal de criar uma nova instancia, ao laterar o método de autenticação para Código de Pareamento, parte do modal fica cortado, não sendo possível vsualizar alguma elementos como o botão: cancelar e criar instância. E bem o botão X para fechar o modal.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 41**: Integração com o Typebot (Módulo: API)
  - **Descrição:** Verificar a possibilidade de abrir um PR no github do Typebot para conseguir integrar com a Uzapi. Temos um público que carece dessa integração.  NÃO CONSEGUI TESTAR COM UMA INSTANCIA DA UZAPI. CONSEGUE ME PASSAR O PASSO A PASSO?
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 43**: Usuário sem planos (Módulo: Assinaturas)
  - **Descrição:** Nota-se usuário sem plano na plataforma da Uzapi. A ideía é que não haja essa categoria. Todos os clientes serão trial. Se não contratarem instancias após o trial, será trial expirado. Mas se contratar instancias, será ativo.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 47**: Sua assinatura vence em 0 dias. (Módulo: Dashboard)
  - **Descrição:** Ao invés de exibir essa mensagem, seria melhor exibir: sua assinatura venceu. Renove agora!
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 49**: Checkout abrindo em uma nova aba (Módulo: Contratar Instâncias)
  - **Descrição:** Recomenda-se abrir o checkout na mesma aba, pois após o pagamento, o mesmo irá voltar para o painel da Uzapi. Do jeito que está atualmnete, o usuário acaba ficando com 2 aba abertas no painel da Uzapi.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 58**: Criar cadastro de clientes estrangeiros (Módulo: Contratar Instâncias)
  - **Descrição:** O Assas liberou para nossa conta a possibilidade de aceitar pagamento de clientes estrangeiros. Nesse caso, assim que o usuário for contratar as primeiras instancias pagas deve ter um checkbox com a label: Não sou residente do Brasil no modal, o qual virá desmarcado por default (false). Se o cliente marcar essa opção (true), o modal não deverá solicitar nem CPF/CNPJ e nem endereço. O cadastro dele como cliente (POST com o endpoint custumer) deve ter o parâmetro foreignCustomer=true. Dessa forma, o Asaas não irá solicitar CPF/CNPJ quando eu for efetua ro pagamento no cartão de crédito.  NÃO VIMOS A OPÇÃO DE MARCAR CLIENTE COMO ESTRANGEIRO NA CONTRATAÇÃO DE INSTANCIAS PAGAS. SÓ MOSTROU CAMPO PARA PREENCHER CPF/CNPJ E O CEP.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 59**: Cobrança Pós-Paga para clientes com SaaS de alta rotatividade (Módulo: Contratar Instâncias)
  - **Descrição:** Verificar a possibilidade de disponibilizar cobrança pós paga para clientes que tem um SaaS onde tem um fluxo grande de clientes testando, mas só uma quantidade que costuma contratar. Considerando a atual estrutura da Uzapi, daria para fazer o seguinte: O cliente poderia informar que quer o sistema de cobrança pós-paga no menu de contratar instancias. Assim, ele teria uma quantidade ilimitada de instancias. Ao chegar no dia do vencimento, a Uzapi faria o cálculo de todas as instãncias que ficaram ativas por mais de 7 dias (dando a entender que são usuários que decidiram assinar o SaaS desse nosso cliente). Dessa forma, esse nosso cliente não precisaria ficarcontratanto lotes de instancias de forma pré-paga para lidar com o fluxo dinamicos de clientes no SaaS dele.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 60**: Data de Vencimento errada para novo usuário (Módulo: Assinaturas)
  - **Descrição:** Após criar uma nova conta de um determinado usuário, verificamos que a data de vencimento aparece corretamnete no dashboard dele (Data Cadastro + 7 dias do teste). Porém na lista de assinaturas (visão admin) mostra a data de vencimento igual data de cadastro
  - 💡 **Solução Sugerida pelo Dev:** 

## 🟢 Prioridade BAIXA

- [ ] **ID 61**: Token da conta com significado errado (Módulo: Meu Perfil)
  - **Descrição:** No token da conta (meu perfil) está sendo informado para usá-lo na autenticaçaõ de chamadas API, quando na verdade deveria informar para ser usado na autenticação da criação de uma nova instancia.
  - 💡 **Solução Sugerida pelo Dev:** 

## 🟢 Prioridade NORMAL

- [ ] **ID 62**: Criação de etiquetas (Módulo: API)
  - **Descrição:** criação de etiquetas
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 64**: Cancelar assinatura do cliente pelo admin (Módulo: Assinaturas)
  - **Descrição:** As vezes, o usuário pode gerar uma assiantura e não efetuar o pagamento e assim ficar inadinplente no Asaas. Isso pode o fazer receber notificações de cobrança de forma desnecessária. Ao invés de pedirmos para o próprio cliente cancelar a assiantura, poderíamos (como admin) cancelar as assianturas deles.
  - 💡 **Solução Sugerida pelo Dev:** 

## 🟢 Prioridade URGENTE

- [ ] **ID 26**: Erro ao redefinir senha (Módulo: Login)
  - **Descrição:** O usuário tentou fazer uma redefinição de senha da conta dele. Ele chega a receber o email, mas ao clicar no botão de redefinir senha, dá um erro de redirecionamento.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 27**: Problema na integração com Chatwoot parte 1 (Módulo: API)
  - **Descrição:** Mensagens trocadas em grupos acaba abrindo conversas no privado entre as 2 pessoas que percente ao mesmo grupo. Ex: Se eu e mais uma pessoas está no grupo, se ela mandar mensagem no grupo, abre uma conversa dela no meu privado.  FOI RESOLVIDO COM A FLAG QUE DESATIVA EVENOS DE GRUPO NAS PROPRIEDADES DE WEBHOOK DA INSTANCIA.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 28**: Problema na integração com Chatwoot parte 2 (Módulo: API)
  - **Descrição:** Quando chamamos um contato pelo WhatsApp aplicativo ou WhatsApp web, o charwoot abr euma conversa com o próprio número ao invés do numero do contato.  FOI RESOLVIDO COM A QUESTÃO DO WEBHOOK NÃO RETORNAR MAIS EVENTOS DE MENSAGENS ENVIADAS PELO WHATSAPP WEB OU WHATSAPP APP. 
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 30**: Não exclui a instancia (Módulo: Instâncias)
  - **Descrição:** Tento excluir a instancia da minha conta e aparece o erro: "r.slice is not a function"..E a instancia não é excluída.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 31**: Problema na integração com Chatwoot parte 3 (Módulo: API)
  - **Descrição:** Após integrar uma instância com o Chatwoot, o mesmo começa a reviver um histórico de várias conversas antigas do numero conectado. E o pior que são conversas sem conteúdo disponivel.  ISSO ERA POR CONTA DOS STATUS DOS CONTATOS DO NUMERO CONECTADO NA API DA UZAPI. EMBORA FOI TRATADO A QUESTÃO DO CONTEÚDO INDISPONÍVEL, FALTA TRATAR ESSE EVENTO DE STATUS PUBLICADOS DOS CONTATOS QUE ACABAM ABRINDO NOVAS CONVERSAS COM CONTEÚDO DESSE STATUS. FALAMOS MAIS SOBRE ISSO NO BUG PROBLEMAS NA INTEGRAÇÃO COM CHATWOOT PARTE 4 (ID 33)
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 33**: Problema na integração do chatwoot parte 4 (Módulo: API)
  - **Descrição:** Ao realizar a integração com o chatwoot, a caixa de entrada começa a receber conteúdos dos status dos contatos como mensagem da conversa privada
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 34**: Não está salvando corretamnete o celular do usuário no cadastro do Asaas (Módulo: Contratar Instâncias)
  - **Descrição:** Quando é criado o cadastro do usuário no Asaas (ao contratar instância pagas), o mesmo não vem com o celular que ele verificou na plataforma da Uzapi.  TESTAMOS E ESTÁ SALVANDO O NUMERO CORRETAMENTE (APENAS DDD + NUMERO)
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 36**: Habilitar envio de audio no formato ogg (Módulo: API)
  - **Descrição:** Não está sendo possivel enviar o audio gravado no whatsapp app/web, pois o endpoint de envia áudio só aceita .mp3  TESTEI COM URL DE AUDIOS OGG  E WAV, MAS SEM SUCESSO. SÓ CONTINUA FUNCIONANDO COM MP3.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 37**: Assinantes indevidamnete com status Trial (Módulo: Assinaturas)
  - **Descrição:** Mesmo após a data de vencimento, alguns assinantes continuam com a assiantura no status Trial.  OBS: PELO QUE NOTEI, O BACKEND ESTÁ RESTRINGIDO O USO DA INSTANCIA. PORÉM SERIA INTERESSANTE QUE ESSE TRATAMENTO TAMBÉM TIVESSE A NÍVEL DE FRONTEND, ONDE AS INSTANCIAS FICASSEM COM O STATUS PAUSADA E SEM PERMITIR UMA NOVA AUTENTICAÇÃO. O USUÁRIO NÃO CONSEGUIRIA CRIAR NOVAS INSTANCIAS. E O STATUS DA ASSIANTURA FOSSE PARA TRIAL-EXPIRADO
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 38**: Assinantes indevidamnete com status Ativo (Módulo: Assinaturas)
  - **Descrição:** Nos casos em que estedemos o prazo Trial do Usuário, faz com que ele fiquei com o status da assinatura igual Ativo mesmo passando da data de vencimento.  OBS: PELO QUE NOTEI, O BACKEND ESTÁ RESTRINGIDO O USO DA INSTANCIA. PORÉM SERIA INTERESSANTE QUE ESSE TRATAMENTO TAMBÉM TIVESSE A NÍVEL DE FRONTEND, ONDE AS INSTANCIAS FICASSEM COM O STATUS PAUSADA E SEM PERMITIR UMA NOVA AUTENTICAÇÃO. O USUÁRIO NÃO CONSEGUIRIA CRIAR NOVAS INSTANCIAS. E O STATUS DA ASSIANTURA FOSSE PARA VENCIDO
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 40**: Documentação não abre para alguns usuários (Módulo: Documentação)
  - **Descrição:** A documentação fica em branco para alguns usuários. Ao pesquisar sobre esse bug do Redocly, diz é que atrelado à um script em javascript da documentação que pode está sendo bloqueeado por alguma extensão ou antivirus/firewall do usuário.  RESOLVIDO! TODOS OS USUÁRIOS AGORA ACESSAM NORMALMNETE A DOCUMENTAÇÃO PRINCIPAL.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 44**: Divergência entre data de vencimento das assianturas no Asaas e na Uzapi (Módulo: Contratar Instâncias)
  - **Descrição:** Quando o usuário contrata instancia pela primeira vez é criado uma assiantura no Assas com a Data Atual + Dias de Cortes.Isso faz com que a data de vencimento na Uzapi fique divergente, pois nela é salvo apenas a data atual, em que o usuário fez a assiantura.  OBS: A DATA DE CORTE NÃO DEVE SER USADA NO CÁLCULO DE DATA DE VENCIMENTO. BASICAMNETE, ELA TEM QUE ATUAR COMO UM CRON QUE IRÁ SE BASEAR NA DATA DE VENCIMENTO DA ASSIANTURA DO CLIENTE (QUE INCLUSIVE TEM QUE SER IDÊNTICAS ENTRE O ASAAS E A UZAPI). OU SEJA, QUANDO CHEGAR NA DATA DE VENCIMENTO, O CLIENTE JÁ É ALERTADO SOBRE A RENOVAÇÃO. MAS QUANDO CHEGAR X DIAS DEPOIS DO VENCIMENTO DELE, A ASSIANTURA É PAUSADA. ESSE BUG TEM RELAÇÃO COM O BUG DE ID 16
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 46**: Retrieve de áudio PTT retorna 410 com “MediaKey (Módulo: API)
  - **Descrição:** Retrieve de áudio PTT retorna 410 com “MediaKey não encontrada” enviei um PDF e o retrieve de PDF funciona, mesmo token, mesmo endpoint, ou seja ou é um race condition ou um bug mais estrutural, que pode ser que recebe o áudio, dispara o webhook com o id, mas internamente não consegue armazenar/recuperar a MediaKey do áudio de voz para servir no retrieve.  TESTEAMOS AQUI E JÁ ESTÁ RETORNANDO ID DA MEDIA DO TIPO AUDIO DE VOZ. RETONA TAMBÉM O MIMETYPE E URL CORRETAMNETE (FORMATO OGG)
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 50**: Falha grave no downgrade de instancias (Módulo: Contratar Instâncias)
  - **Descrição:** Testei com um usuário que tinha 2 instancias ativas. Fiz o downgrade para 1 instancia. Ainda sim, as 2 instancias do usuário continuaram ativas e funcionando perfeitamnete. O Dashboard estava exibindo: 2/1 instancias ativas Ou seja, permitindo o usuário usar 2 instancias mesmo em um plano de 1 instancia.  TESTAMOS E REALMNETE IMPEDIU O DOWNGRADE AO TER QUANTIDADE DE INSTANCIAS CRIADAS MAIOR QUE  A QUANTIDADE DE INSTANCIA DO DOWNGRADE.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 52**: Liberacao ou correcao do endpoint de documentos
ZIP (Módulo: API)
  - **Descrição:** liberação/correção do download de documentos ZIP recebidos pelo WhatsApp através  O webhook recebe corretamente a mensagem do tipo document, contendo: document.id filename sha256 mime_type: application/zip ou application/x-zip-compressed  Conforme a documentação, utilizamos o endpoint: GET /{username}/v1/{mediaId} com o token válido da instância. Entretanto, para arquivos ZIP, ofx, exe ou pfx, a API responde: HTTP 410: unsupported file type for download PDF, imagens e outros formatos funcionam. Testamos arquivos diretos ou ZIP com conteúdos, tamanhos e quantidades de arquivos diferentes, mas todos retornaram o mesmo erro. Solicitamos que habilitem os tipos MIME application/zip e application/x-zip-compressed no endpoint de recuperação de mídia, ou informem uma rota alternativa para baixar esses documentos. Podem verificar a instância da conta lunarhouse. Por segurança, enviaremos o phone_number_id, mediaId e token somente em atendimento privado, caso sejam necessários.  TESTAMOS COM A INSTANCIA NA VERSÃO 0.088 E JÁ RETORNANDO URL DO ARQUIVO NA EXTENSÃO .ZIP.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 57**: Erro 500 ao fazer upload de mídia (Módulo: API)
  - **Descrição:** Ao tentar um upload de midia, a API retorna erro 500 (Erro interno ao fazer upload da midia). A principio estava funcionando, mas nos ultimos dias para cá começou a apresentar esse erro.  TESTAMOS E JÁ ESTÁ FAZENDO O UPLOAD DAS MIDIAS.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 65**: Audios enviados não reproduzem no iPhone (Módulo: API)
  - **Descrição:** Ao enviar audio para um whatsapp do iPhone, o mesmo não consegue repoduzir. Exibe o erro: Esse áudio não está mais disponível. Peça a [NUM-DESTINATARIO] para reenviá-lo.
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 66**: Notificações são enviadas mesmo desativadas (Módulo: Notificações)
  - **Descrição:** Desativamos as notificações Trial Expirando (D-3) e mesmo assim ela continuam sendo enviadas às 06:05AM
  - 💡 **Solução Sugerida pelo Dev:** 

- [ ] **ID 68**: Instancia expirando mesmo com assiantura ativa (Módulo: Contratar Instâncias)
  - **Descrição:** Pegamos um caso aqui, onde o cliente estava com a instancia expirada, mesmo com a assinatura ativa. Acredito que se tratava de uma instancia criad ano período de trial e após a assiantura, a plataforma não renovou a data de expiração da instancia.
  - 💡 **Solução Sugerida pelo Dev:** 

