# Projekt-3-rok-I-semestr - backend

Repozytorium projektowe odpowiadające za backend.

Zespół:
| Imie       | Role                      |
| ---------- | ------------------------- |
| Paweł.D    | backend / devops          |
| Tobiasz.J  | PM / Tester               |
| Kacper.B   | Frontend / PM / Tester    |
| Grzegorz.S | Backend / devops / Tester |

Opis projektu:

# Platforma zgłaszania i obsługi usterek infrastruktury miejskiej

**Opis aplikacji**

Aplikacja webowa umożliwiająca mieszkańcom zgłaszanie problemów z infrastrukturą miejską (uszkodzone latarnie, dziury w drogach, zniszczone znaki i ławki, nielegalne śmieci) oraz śledzenie postępu ich naprawy. Zgłoszenia trafiają do pracowników urzędu, którzy zarządzają ich realizacją, a cały proces jest jawny dla mieszkańców.

**Główne funkcje**

- **Konta użytkowników:** rejestracja klasyczna (e-mail i hasło) oraz przez zewnętrznego dostawcę OAuth (np. Google).
- **Mapa zgłoszeń:** interaktywna mapa z wszystkimi zgłoszonymi problemami, widoczna dla użytkowników.
- **Nowe zgłoszenie:** wskazanie miejsca na mapie lub użycie geolokalizacji, wybór kategorii, opis i zdjęcia.
- **Wykrywanie duplikatów:** przed dodaniem zgłoszenia system wyszukuje podobne zgłoszenia w pobliżu (z uwzględnieniem odległości geograficznej i kategorii). Użytkownik może wybrać „ten problem również mnie dotyczy” zamiast tworzyć duplikat.
- **Obserwowanie zgłoszeń:** użytkownicy obserwują wybrane zgłoszenia i dostają powiadomienia o zmianie ich statusu.
- **Obsługa przez urząd:** pracownik zmienia status (zgłoszone → przyjęte → przekazane do realizacji → w realizacji → rozwiązane / odrzucone), dodaje publiczne komentarze i zdjęcie po naprawie.
- **Statystyki publiczne:** liczba zgłoszeń według kategorii, średni czas realizacji, liczba rozwiązanych zgłoszeń.
- **Panel administratora:** mapa obszarów z największą liczbą zgłoszeń (heatmapa), zarządzanie użytkownikami i kategoriami, podgląd logów aplikacji.

**Role w systemie**

| Rola | Uprawnienia |
|---|---|
| Użytkownik | zgłaszanie, obserwowanie, potwierdzanie problemów, przeglądanie mapy i statystyk |
| Pracownik urzędu | zmiana statusów, komentarze, zdjęcia po naprawie |
| Administrator | wszystko powyżej oraz zarządzanie użytkownikami, kategoriami, logami i mapą koncentracji zgłoszeń |

##Współpraca

Zasady pracy z repozytorium (proces pull requestów, nazewnictwo gałęzi, konwencja commitów, przegląd kodu) są wspólne dla wszystkich repozytoriów projektu i opisane w dokumencie [CONTRIBUTING.md](https://github.com/januszex-ai/.github/blob/main/CONTRIBUTING.md).

Zadania i postęp sprintów śledzimy na [tablicy projektu](https://github.com/orgs/januszex-ai/projects/1).

Stack Technologiczny:

Link do Figma:




