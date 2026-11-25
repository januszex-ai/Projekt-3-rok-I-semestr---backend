# Serwer staging – runbook

Dokument opisuje konfigurację maszyny wirtualnej w Microsoft Azure, na której działa backend w środowisku testowym (staging). Celem jest to, aby każdy członek zespołu mógł zrozumieć, jak serwer jest zbudowany, i w razie potrzeby odtworzyć go od zera.

> ⚠️ **W tym dokumencie nigdy nie zapisujemy kluczy prywatnych, haseł, tokenów ani adresów e-mail.** Repozytorium jest publiczne. Dane dostępowe przekazujemy wyłącznie kanałami prywatnymi.

---

## Spis treści

1. [Dane środowiska](#1-dane-środowiska)
2. [Dostęp do serwera](#2-dostęp-do-serwera)
3. [Architektura i zabezpieczenia](#3-architektura-i-zabezpieczenia)
4. [Konfiguracja krok po kroku](#4-konfiguracja-krok-po-kroku)
5. [Weryfikacja](#5-weryfikacja)
6. [Utrzymanie](#6-utrzymanie)
7. [Rozwiązywanie problemów](#7-rozwiązywanie-problemów)
8. [Odtworzenie serwera od zera](#8-odtworzenie-serwera-od-zera)

---

## 1. Dane środowiska

| Parametr | Wartość |
|---|---|
| Dostawca | Microsoft Azure (subskrypcja Azure for Students) |
| Region | Belgium Central |
| Grupa zasobów | `rg-projekt3-staging` |
| Nazwa maszyny | `vm-projekt3-staging` |
| Rozmiar | `<B2als v2>` (seria B, 2 GB RAM) |
| System | Ubuntu Server 24.04 LTS (x64, Gen2) |
| Dysk | Standard SSD (LRS), 30 GB |
| Domena | `menelapp.belgiumcentral.cloudapp.azure.com` |
| Publiczny adres IP | statyczny (Standard SKU), widoczny w portalu: VM → Overview |
| Otwarte porty | 22 (SSH), 80 (HTTP), 443 (HTTPS) |
| Strefa czasowa | Europe/Warsaw |
| Certyfikat SSL | Let's Encrypt (Certbot), automatyczne odnawianie |
| Katalog aplikacji | `/home/deploy/backend` (tworzony w B-5) |

Domena pochodzi z etykiety DNS publicznego adresu IP w Azure, więc nie wymaga kupowania własnej.

---

## 2. Dostęp do serwera

### Konta na serwerze

| Konto | Uprawnienia | Przeznaczenie |
|---|---|---|
| `azureuser` | sudo | administracja serwerem (aktualizacje, firewall, certyfikaty) |
| `deploy` | bez sudo, grupa `docker` | wdrażanie aplikacji (GitHub Actions, B-5) |

Logowanie wyłącznie kluczem SSH. Logowanie hasłem i jako `root` jest wyłączone.

### Osoby z dostępem administracyjnym

| Osoba | Login GitHub | Konto |
|---|---|---|
| `<imię i nazwisko>` | `<login>` | `azureuser` |

Nowa osoba dostaje dostęp po dopisaniu jej **klucza publicznego** do `~/.ssh/authorized_keys` odpowiedniego konta. Każda osoba ma własny klucz; nie współdzielimy kluczy prywatnych.

### Konfiguracja klienta SSH

Klucz prywatny trzymamy w `~/.ssh/` z uprawnieniami `600`:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/azure_staging
```

Wpis w `~/.ssh/config` na komputerze dewelopera:

```
Host staging
    HostName menelapp.belgiumcentral.cloudapp.azure.com
    User azureuser
    IdentityFile ~/.ssh/azure_staging
    IdentitiesOnly yes

Host staging-deploy
    HostName menelapp.belgiumcentral.cloudapp.azure.com
    User deploy
    IdentityFile ~/.ssh/azure_staging
    IdentitiesOnly yes
```

Połączenie:

```bash
ssh staging
```

- Alias (`Host`) działa tylko przy łączeniu przez jego nazwę (`ssh staging`). Wpisanie pełnej domeny pomija ustawienia z configu.
- `IdentitiesOnly yes` sprawia, że SSH próbuje tylko wskazanego klucza. Bez tego przy wielu kluczach w agencie łatwo przekroczyć limit prób i dostać bana od fail2ban.
- Przy pierwszym połączeniu SSH zapyta o odcisk klucza serwera – należy wpisać `yes`. Jeśli pytanie pojawi się ponownie dla tego samego serwera, coś się zmieniło (serwer odtworzony albo próba podszycia się) – najpierw ustal przyczynę.

---

## 3. Architektura i zabezpieczenia

Backend działa w kontenerach Docker na pojedynczej maszynie wirtualnej. Wybraliśmy maszynę wirtualną zamiast usług zarządzanych (App Service, zarządzany MySQL) ze względu na koszt, zgodność ze środowiskiem lokalnym (ten sam Docker Compose) i wartość edukacyjną. Konsekwencją jest to, że za bezpieczeństwo systemu odpowiadamy sami.

Serwer chroni kilka niezależnych warstw (obrona warstwowa):

| Warstwa | Rola |
|---|---|
| Network Security Group (Azure) | firewall w chmurze; ruch spoza portów 22/80/443 nie dociera do maszyny |
| ufw | firewall systemowy, druga warstwa |
| SSH tylko na klucze | ataki na hasła są bezcelowe |
| fail2ban | automatyczne blokowanie adresów po nieudanych próbach logowania |
| osobne konto `deploy` | wyciek klucza CI nie daje uprawnień sudo |
| unattended-upgrades | automatyczne łatanie znanych luk bezpieczeństwa |

**Docker omija ufw.** Port opublikowany przez Dockera (`ports:`) jest dostępny niezależnie od reguł ufw. Dlatego:
- nadrzędną ochroną jest NSG, na którą Docker nie ma wpływu,
- w konfiguracji produkcyjnej baza danych **nie publikuje żadnego portu**.

Konto `deploy` w grupie `docker` ma w praktyce szerokie uprawnienia (dostęp do demona Dockera), dlatego jego klucz traktujemy jako dane uprzywilejowane.

---

## 4. Konfiguracja krok po kroku

Kroki 4.1–4.2 wykonujemy w portalu Azure, pozostałe na serwerze jako `azureuser`.

### 4.1. Utworzenie maszyny wirtualnej (portal Azure)

**Virtual machines → Create → Azure virtual machine**

| Zakładka | Ustawienie |
|---|---|
| Basics | grupa zasobów `rg-projekt3-staging`, nazwa `vm-projekt3-staging`, region Belgium Central, bez redundancji, Trusted launch, Ubuntu Server 24.04 LTS x64 Gen2, rozmiar serii B z 2 GB RAM |
| Basics – administrator | SSH public key, użytkownik `azureuser`, klucz publiczny administratora |
| Basics – porty | Allow selected ports: 22, 80, 443 |
| Disks | Standard SSD (LRS), Delete with VM |
| Networking | nowe VNet, publiczny IP Standard, NSG Basic (22/80/443), usuwanie IP i NIC razem z VM |
| Management | Auto-shutdown wyłączony |
| Tags | `project=projekt3`, `environment=staging` |

*Dlaczego:* seria B (burstable) pasuje do stagingu, który przez większość czasu jest bezczynny; Standard SSD wystarcza wydajnościowo przy kilkukrotnie niższej cenie niż Premium; tagi pozwalają filtrować koszty projektu.

> Subskrypcje studenckie mogą mieć ograniczoną listę regionów. W razie błędu wybierz najbliższy dozwolony region i zaktualizuj ten dokument.

### 4.2. Domena (etykieta DNS)

VM → Overview → kliknij publiczny adres IP → **Settings → Configuration → DNS name label** → `menelapp` → Save.

*Dlaczego:* stała domena jest potrzebna do certyfikatu SSL, a frontend na HTTPS nie może odpytywać API po HTTP.

Sprawdzenie (z własnego komputera):

```bash
nslookup menelapp.belgiumcentral.cloudapp.azure.com
```

> `ping` nie działa i to jest prawidłowe – NSG nie przepuszcza ICMP.

### 4.3. Aktualizacja systemu i strefa czasowa

```bash
sudo apt update && sudo apt full-upgrade -y
sudo timedatectl set-timezone Europe/Warsaw
sudo reboot
```

*Dlaczego:* obraz systemu bywa sprzed kilku tygodni i może zawierać załatane już luki; polska strefa czasowa ułatwia czytanie logów.

### 4.4. Konto `deploy`

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

*Dlaczego:* deployment działa na osobnym koncie bez sudo i bez hasła (zasada najmniejszych uprawnień). Klucz administratora kopiujemy tylko do weryfikacji logowania; w B-5 dochodzi tu osobny klucz GitHub Actions.

### 4.5. Utwardzenie SSH

```bash
sudo tee /etc/ssh/sshd_config.d/00-hardening.conf > /dev/null <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
AllowUsers azureuser deploy
EOF

sudo sshd -t && sudo systemctl restart ssh
sudo sshd -T | grep -E 'passwordauthentication|permitrootlogin|allowusers'
```

*Dlaczego:* logowanie wyłącznie kluczem i tylko na wskazane konta eliminuje ataki słownikowe. Plik ma prefiks `00-`, bo przy powtarzającej się opcji SSH stosuje **pierwszą** wczytaną wartość, a obraz Azure zawiera plik `50-cloud-init.conf`, który mógłby nadpisać nasze ustawienia.

> ⚠️ Nie zamykaj bieżącej sesji, dopóki w nowym terminalu nie potwierdzisz, że logowanie działa.

### 4.6. Firewall systemowy (ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

*Dlaczego:* domyślna blokada ruchu przychodzącego sprawia, że nowa usługa nie stanie się publiczna przez przypadek. Reguła `OpenSSH` musi zostać dodana przed `ufw enable`.

### 4.7. fail2ban

```bash
sudo apt install -y fail2ban python3-systemd

sudo tee /etc/fail2ban/jail.local > /dev/null <<'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
backend = systemd
EOF

sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

*Dlaczego:* serwer jest stale skanowany przez boty; fail2ban blokuje na godzinę adresy z serią nieudanych logowań. `backend = systemd`, bo Ubuntu 24.04 przechowuje logi SSH w journald.

### 4.8. Automatyczne aktualizacje bezpieczeństwa

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

sudo tee /etc/apt/apt.conf.d/52unattended-upgrades-local > /dev/null <<'EOF'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
EOF

sudo unattended-upgrade --dry-run --debug 2>&1 | tail -n 5
```

*Dlaczego:* łatki bezpieczeństwa instalują się bez udziału człowieka; restart (gdy wymaga go aktualizacja jądra) odbywa się o 4:00, a kontenery z `restart: unless-stopped` uruchamiają się ponownie same.

### 4.9. Pamięć swap

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
sudo sysctl --system
free -h
```

*Dlaczego:* swap chroni MySQL przed zatrzymaniem przy chwilowym braku pamięci; `swappiness=10` sprawia, że system sięga po niego tylko w ostateczności.

### 4.10. Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy

sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
sudo systemctl enable docker containerd
```

*Dlaczego:* Docker uruchamia aplikację tak samo jak lokalnie. Rotacja logów ogranicza logi do 30 MB na kontener – bez niej logi potrafią zapełnić dysk i zatrzymać cały serwer.

> `azureuser` nie należy do grupy `docker` i używa Dockera przez `sudo`. Komunikat `permission denied` bez `sudo` jest zamierzony.

### 4.11. Certyfikat SSL (Let's Encrypt)

```bash
sudo apt install -y certbot

sudo certbot certonly --standalone \
  -d menelapp.belgiumcentral.cloudapp.azure.com \
  -m <email-osoby-odpowiedzialnej-za-infrastrukture> --agree-tos --no-eff-email \
  --pre-hook "docker compose -f /home/deploy/backend/docker-compose.prod.yml stop nginx || true" \
  --post-hook "docker compose -f /home/deploy/backend/docker-compose.prod.yml start nginx || true"

sudo certbot certificates
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
```

*Dlaczego:* API musi działać po HTTPS. Tryb `--standalone` na chwilę uruchamia własny serwer na porcie 80, aby potwierdzić kontrolę nad domeną. Hooki zatrzymują i wznawiają kontener Nginx podczas automatycznego odnawiania (co ok. 60 dni).

Uwagi:
- Dopóki nie istnieje `docker-compose.prod.yml` (B-5), hooki wypisują błąd `no such file or directory`. Jest to oczekiwane – `|| true` sprawia, że nie przerywa to Certbota.
- **Ścieżka `/home/deploy/backend` jest umową z B-5.** Jeśli repozytorium zostanie sklonowane w inne miejsce, należy poprawić `pre_hook` i `post_hook` w `/etc/letsencrypt/renewal/menelapp.belgiumcentral.cloudapp.azure.com.conf`.
- Let's Encrypt nie wysyła przypomnień o wygasających certyfikatach, dlatego odnawianie musi działać automatycznie (`certbot.timer`).
- Zmiana adresu e-mail konta: `sudo certbot update_account --email <nowy-adres>`.

### 4.12. Budżet i alerty kosztów (portal Azure)

**Cost Management + Billing → Cost Management → Budgets → Add**

| Pole | Wartość |
|---|---|
| Scope | subskrypcja Azure for Students |
| Name | `budzet-projekt3` |
| Reset period | Monthly |
| Amount | `<kwota>` USD (kredyt podzielony przez liczbę miesięcy projektu) |
| Alerty | 50%, 80%, 100% (Actual) |
| Odbiorcy | co najmniej dwie osoby z zespołu |

*Dlaczego:* po wyczerpaniu kredytu Azure wyłącza zasoby i staging przestaje działać. Alerty dają czas na reakcję.

---

## 5. Weryfikacja

Z komputera dewelopera:

```bash
nslookup menelapp.belgiumcentral.cloudapp.azure.com     # zwraca adres IP serwera
ssh -o PubkeyAuthentication=no azureuser@menelapp.belgiumcentral.cloudapp.azure.com
                                                         # Permission denied (publickey)
ssh root@menelapp.belgiumcentral.cloudapp.azure.com      # Permission denied
nc -zv -w 3 menelapp.belgiumcentral.cloudapp.azure.com 3306
                                                         # timeout / refused
```

Na serwerze:

```bash
sudo ufw status                                   # 22, 80, 443 – ALLOW
sudo fail2ban-client status sshd                  # jail aktywny
systemctl status unattended-upgrades --no-pager   # active
free -h                                           # Swap: 2.0Gi
sudo docker info --format '{{.LoggingDriver}}'    # json-file
sudo certbot certificates                         # certyfikat ważny
sudo -iu deploy docker ps                         # działa bez sudo
```

---

## 6. Utrzymanie

| Czynność | Częstotliwość | Polecenie / miejsce |
|---|---|---|
| Sprawdzenie kosztów | co tydzień | portal: Cost Management → Cost analysis |
| Przegląd zablokowanych adresów | wg potrzeb | `sudo fail2ban-client status sshd` |
| Sprawdzenie odnawiania certyfikatu | po zmianach w konfiguracji | `sudo certbot renew --dry-run` |
| Sprawdzenie miejsca na dysku | co tydzień | `df -h` |
| Logi systemowe SSH | wg potrzeb | `sudo journalctl -u ssh --since today` |
| Dodanie osoby do zespołu | wg potrzeb | dopisanie klucza publicznego do `~/.ssh/authorized_keys` i aktualizacja sekcji 2 |
| Odebranie dostępu | gdy osoba opuszcza projekt | usunięcie jej klucza z `authorized_keys` i aktualizacja sekcji 2 |

---

## 7. Rozwiązywanie problemów

### Diagnoza połączenia SSH

```bash
ssh -v staging
```

| Komunikat | Przyczyna | Rozwiązanie |
|---|---|---|
| `Could not resolve hostname` | domena nie działa | sprawdź etykietę DNS; połącz się po IP |
| `Connection timed out` | ruch nie dociera | VM uruchomiona? reguła portu 22 w NSG? sieć lokalna blokuje port 22? ban fail2ban? |
| `Connection refused` | SSH nie działa | `systemctl status ssh`, `sshd -t` (przez Run command) |
| `Permission denied (publickey)` | zły klucz lub użytkownik | sprawdź `IdentityFile` i `User`; łącz się przez alias |
| `Host key verification failed` | nie potwierdzono odcisku serwera | wpisz `yes` przy pierwszym połączeniu |

### Dostęp awaryjny bez SSH

Portal: VM → **Operations → Run command → RunShellScript** (polecenia wykonują się jako root):

```bash
ufw allow OpenSSH
ufw status
fail2ban-client unban --all || true
sshd -t && systemctl restart ssh
sshd -T | grep -E 'passwordauthentication|allowusers|permitrootlogin'
```

Utrata klucza administratora: VM → **Help → Reset password → Reset SSH public key** (użytkownik `azureuser`).

Ostateczność: VM → **Help → Serial console**.

---

## 8. Odtworzenie serwera od zera

Dane na stagingu są testowe i nie są objęte kopią zapasową. W razie awarii, utraty kredytu lub przeniesienia do innego regionu serwer odtwarzamy według poniższej listy (szacowany czas: ok. 1 godzina).

1. **Usunięcie starych zasobów (jeśli istnieją):** portal → grupa zasobów `rg-projekt3-staging` → Delete resource group. Usuwa maszynę, dysk, adres IP, NSG i sieć jednocześnie.
2. **Nowa maszyna:** kroki [4.1](#41-utworzenie-maszyny-wirtualnej-portal-azure) i [4.2](#42-domena-etykieta-dns). Jeśli etykieta DNS `menelapp` jest jeszcze zajęta przez usuwany adres, odczekaj kilka minut.
3. **Konfiguracja systemu:** kroki [4.3](#43-aktualizacja-systemu-i-strefa-czasowa)–[4.10](#410-docker) w podanej kolejności.
4. **Certyfikat:** krok [4.11](#411-certyfikat-ssl-lets-encrypt).
5. **Budżet:** krok [4.12](#412-budżet-i-alerty-kosztów-portal-azure) – tylko jeśli powstała nowa subskrypcja.
6. **Klienci SSH:** każda osoba usuwa stary odcisk serwera, aby uniknąć ostrzeżenia o zmianie klucza:
   ```bash
   ssh-keygen -R menelapp.belgiumcentral.cloudapp.azure.com
   ```
7. **Aplikacja:** wdrożenie zgodnie z procedurą z B-5 (klucz GitHub Actions dla konta `deploy`, sklonowanie repozytorium do `/home/deploy/backend`, plik `.env` stagingu, pierwsze uruchomienie).
8. **Weryfikacja:** sekcja [5](#5-weryfikacja).
9. **Aktualizacja dokumentu:** jeśli zmieniła się domena, region, rozmiar lub adres IP – popraw sekcję 1 oraz sekrety repozytorium używane przez deployment (`SSH_HOST`).

---

*Ostatnia aktualizacja: <data> – <autor>*
