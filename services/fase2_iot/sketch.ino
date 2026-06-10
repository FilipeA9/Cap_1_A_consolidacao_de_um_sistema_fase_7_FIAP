// Sistema de Irrigação Inteligente - FarmTech Solutions
// Monitora NPK, pH e Umidade para controle automatizado de irrigação

#include <DHT.h>

// ===== DEFINIÇÃO DOS PINOS =====
#define RELE_PIN 23        // Relé da bomba d'água
#define DHT_PIN 15         // Sensor DHT22 (umidade)
#define BOTAO_N 13         // Botão Nitrogênio
#define BOTAO_P 12         // Botão Fósforo
#define BOTAO_K 14         // Botão Potássio
#define LDR_PIN 34         // Sensor LDR (pH)

// ===== CONFIGURAÇÃO DO DHT22 =====
#define DHTTYPE DHT22
DHT dht(DHT_PIN, DHTTYPE);

// ===== VARIÁVEIS GLOBAIS =====
bool nivelN = false;       // Nível de Nitrogênio
bool nivelP = false;       // Nível de Fósforo
bool nivelK = false;       // Nível de Potássio
float umidade = 0;         // Umidade do solo (%)
int valorPH = 0;           // Valor do pH (simulado pelo LDR)
bool bombaLigada = false;  // Estado da bomba

// ===== INTEGRAÇÃO COM PYTHON - PREVISÃO CLIMÁTICA =====
int previsaoChuva = 1;     // 1 = Sem chuva (permite irrigação)
                           // 0 = Chuva prevista (suspende irrigação)

// ===== PARÂMETROS DE IRRIGAÇÃO =====
// Ajuste esses valores conforme a cultura agrícola escolhida
const float UMIDADE_MINIMA = 60.0;     // Umidade mínima ideal (%)
const int PH_MINIMO = 1500;            // pH mínimo ideal (escala do LDR: 0-4095)
const int PH_MAXIMO = 2500;            // pH máximo ideal

void setup() {
  // Inicializa comunicação serial
  Serial.begin(115200);
  Serial.println("=== Sistema de Irrigação Inteligente ===");
  Serial.println("FarmTech Solutions - Fase 3");
  Serial.println("Integração com Previsão Climática");
  Serial.println();

  // Configura os pinos
  pinMode(RELE_PIN, OUTPUT);
  pinMode(BOTAO_N, INPUT_PULLUP);
  pinMode(BOTAO_P, INPUT_PULLUP);
  pinMode(BOTAO_K, INPUT_PULLUP);
  pinMode(LDR_PIN, INPUT);

  // Desliga a bomba inicialmente
  digitalWrite(RELE_PIN, LOW);

  // Inicializa o sensor DHT22
  dht.begin();
  
  delay(2000); // Aguarda estabilização dos sensores
  Serial.println("Sistema inicializado com sucesso!");
  Serial.println("------------------------------------------");
  Serial.println("💡 INTEGRAÇÃO PYTHON:");
  Serial.println("   Digite '0' = Chuva prevista (suspende irrigação)");
  Serial.println("   Digite '1' = Sem chuva (permite irrigação)");
  Serial.println("==========================================");
}

void loop() {
  // ===== LEITURA DE DADOS DA INTEGRAÇÃO PYTHON =====
  lerPrevisaoClima();
  
  // ===== LEITURA DOS SENSORES =====
  lerSensores();
  
  // ===== EXIBE DADOS NO MONITOR SERIAL =====
  exibirDados();
  
  // ===== LÓGICA DE DECISÃO DE IRRIGAÇÃO =====
  decidirIrrigacao();
  
  // ===== CONTROLA A BOMBA =====
  controlarBomba();
  
  Serial.println("==========================================");
  delay(3000); // Atualiza a cada 3 segundos
}

void lerPrevisaoClima() {
  // Verifica se há dados disponíveis no Serial Monitor
  if (Serial.available() > 0) {
    char dadoRecebido = Serial.read();
    
    // Limpa buffer serial
    while(Serial.available() > 0) {
      Serial.read();
    }
    
    // Processa o dado recebido
    if (dadoRecebido == '0') {
      previsaoChuva = 0;
      Serial.println("\n🌧️  PYTHON: Chuva prevista! Irrigação será SUSPENSA");
    } 
    else if (dadoRecebido == '1') {
      previsaoChuva = 1;
      Serial.println("\n☀️  PYTHON: Sem chuva prevista. Irrigação PERMITIDA");
    }
    else {
      Serial.println("\n⚠️  Valor inválido! Use apenas 0 ou 1");
    }
    Serial.println();
  }
}

void lerSensores() {
  // Lê os botões NPK (LOW = pressionado, HIGH = não pressionado)
  nivelN = !digitalRead(BOTAO_N);
  nivelP = !digitalRead(BOTAO_P);
  nivelK = !digitalRead(BOTAO_K);
  
  // Lê a umidade do DHT22
  umidade = dht.readHumidity();
  if (isnan(umidade)) {
    umidade = 0;
    Serial.println("Erro ao ler DHT22!");
  }
  
  // Lê o pH pelo LDR (valores de 0 a 4095)
  valorPH = analogRead(LDR_PIN);
}

void exibirDados() {
  Serial.println("📊 DADOS DOS SENSORES:");
  Serial.println("------------------------------------------");
  
  // Nutrientes
  Serial.print("🔬 Nitrogênio (N): ");
  Serial.println(nivelN ? "✅ ADEQUADO" : "❌ BAIXO");
  
  Serial.print("🔬 Fósforo (P): ");
  Serial.println(nivelP ? "✅ ADEQUADO" : "❌ BAIXO");
  
  Serial.print("🔬 Potássio (K): ");
  Serial.println(nivelK ? "✅ ADEQUADO" : "❌ BAIXO");
  
  // pH
  Serial.print("⚗️  pH do Solo: ");
  Serial.print(valorPH);
  if (valorPH >= PH_MINIMO && valorPH <= PH_MAXIMO) {
    Serial.println(" ✅ IDEAL");
  } else {
    Serial.println(" ⚠️ FORA DA FAIXA");
  }
  
  // Umidade
  Serial.print("💧 Umidade do Solo: ");
  Serial.print(umidade);
  Serial.println("%");
  
  // Previsão Climática
  Serial.print("🌤️  Previsão Clima: ");
  if (previsaoChuva == 0) {
    Serial.println("🌧️ CHUVA PREVISTA");
  } else {
    Serial.println("☀️ SEM CHUVA");
  }
  
  Serial.println("------------------------------------------");
}

void decidirIrrigacao() {
  Serial.println("🤖 ANÁLISE DE IRRIGAÇÃO:");
  
  // Verifica se todos os nutrientes estão adequados
  bool nutrientesOK = nivelN && nivelP && nivelK;
  
  // Verifica se o pH está na faixa ideal
  bool pHOK = (valorPH >= PH_MINIMO && valorPH <= PH_MAXIMO);
  
  // Verifica se a umidade está baixa
  bool umidadeBaixa = (umidade < UMIDADE_MINIMA);
  
  // Verifica previsão climática (integração Python)
  bool semChuva = (previsaoChuva == 1);
  
  // Exibe análise detalhada
  Serial.print("   Nutrientes NPK: ");
  Serial.println(nutrientesOK ? "✅ OK" : "⚠️ Insuficientes");
  
  Serial.print("   pH do Solo: ");
  Serial.println(pHOK ? "✅ OK" : "⚠️ Fora da faixa");
  
  Serial.print("   Umidade: ");
  Serial.println(umidadeBaixa ? "⚠️ BAIXA - Necessita irrigação" : "✅ Adequada");
  
  Serial.print("   Previsão Clima: ");
  Serial.println(semChuva ? "✅ Sem chuva" : "🌧️ CHUVA PREVISTA - Bloqueia irrigação");
  
  // LÓGICA DE DECISÃO ATUALIZADA (FASE 3):
  // Liga a bomba SE:
  // 1. Umidade está baixa E
  // 2. Nutrientes estão adequados E
  // 3. pH está na faixa ideal E
  // 4. SEM previsão de chuva (integração Python)
  
  if (umidadeBaixa && nutrientesOK && pHOK && semChuva) {
    bombaLigada = true;
    Serial.println("🚰 DECISÃO: LIGAR IRRIGAÇÃO");
    Serial.println("   Motivo: Condições ideais para irrigação");
  } else {
    bombaLigada = false;
    Serial.println("🛑 DECISÃO: DESLIGAR IRRIGAÇÃO");
    
    if (!semChuva) {
      Serial.println("   Motivo: ☔ CHUVA PREVISTA - Economizando recursos");
    } else if (!umidadeBaixa) {
      Serial.println("   Motivo: Umidade adequada");
    } else if (!nutrientesOK) {
      Serial.println("   Motivo: Nutrientes insuficientes");
    } else if (!pHOK) {
      Serial.println("   Motivo: pH fora da faixa ideal");
    }
  }
}

void controlarBomba() {
  if (bombaLigada) {
    digitalWrite(RELE_PIN, HIGH); // Liga o relé (bomba)
    Serial.println("💦 STATUS: BOMBA LIGADA ✅");
  } else {
    digitalWrite(RELE_PIN, LOW);  // Desliga o relé (bomba)
    Serial.println("⭕ STATUS: BOMBA DESLIGADA");
  }
}