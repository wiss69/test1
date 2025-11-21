# TicketZen

TicketZen est une application Flask légère pour l'acquisition et l'analyse de tickets de caisse ou factures. Le projet est conçu pour être cross-platform (Windows/macOS) avec un démarrage simple via `python main.py`. L'OCR privilégie Azure Document Intelligence avec des mécanismes de repli et un mode hors-ligne/dry-run.

## Démarrage rapide

### Windows (PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # puis éditer et mettre tes valeurs
python main.py
```

### macOS (zsh)
```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis éditer et mettre tes valeurs
python main.py
```

### Vérifier Azure (v2.1)
```bash
curl -s -D - -H "Ocp-Apim-Subscription-Key: $AZURE_DI_KEY" \
  -H "Content-Type: image/png" --data-binary "@sample.png" \
  "$AZURE_DI_ENDPOINT/formrecognizer/v2.1/prebuilt/receipt/analyze?includeTextDetails=true"
```

## Sécurité & configuration

- Aucune clé ou secret n'est committé ; renseignez vos valeurs dans `.env` ou les variables d'environnement.
- Les routes API renvoient toujours un JSON HTTP 200 structurés `{ok: bool, error?: string}` pour éviter les échecs côté front.

## Arborescence

Consultez `main.py` et `app/core/server.py` pour le serveur Flask, `addons/intake/api.py` pour le flux d'import, `addons/ocr/providers/azure_client.py` pour le client Azure, ainsi que les templates HTML dans `app/templates`.
