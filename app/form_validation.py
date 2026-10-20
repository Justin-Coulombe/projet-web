"""Validation centralisée des formulaires ParkShare (indépendante du navigateur)."""
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from PIL import Image, UnidentifiedImageError

CITIES = {
    'Montréal', 'Québec', 'Laval', 'Gatineau', 'Longueuil',
    'Sherbrooke', 'Lévis', 'Saguenay', 'Trois-Rivières', 'Terrebonne',
    'Saint-Jean-sur-Richelieu', 'Brossard', 'Repentigny',
    'Saint-Jérôme', 'Drummondville'
}
MAX_PHOTO = 2 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000
EMAIL = re.compile(r'^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$')


def valider_identite(data, *, prenom=True, nom=True, email=True):
    clean, errors = {}, {}
    for field, enabled in [('prenom', prenom), ('nom', nom)]:
        if not enabled:
            continue
        value = str(data.get(field, '')).strip()
        if not 2 <= len(value) <= 80 or not all(c.isalpha() or c in " '-" for c in value):
            errors[field] = 'Entre 2 et 80 caractères : lettres, espaces, apostrophes ou tirets.'
        else:
            clean[field] = value
    if email:
        value = str(data.get('email', '')).strip().lower()
        if not 3 <= len(value) <= 254 or not EMAIL.fullmatch(value):
            errors['email'] = 'Entrez une adresse courriel valide.'
        else:
            clean['email'] = value
    return clean, errors


def valider_mot_de_passe(value, field='password'):
    if not isinstance(value, str) or not 8 <= len(value) <= 128 or '\x00' in value:
        return {field: 'Le mot de passe doit contenir entre 8 et 128 caractères.'}
    return {}


def valider_stationnement(data):
    clean, errors = {}, {}
    adresse = str(data.get('adresse') or '').strip()
    if not 5 <= len(adresse) <= 200 or any(ord(c) < 32 for c in adresse):
        errors['adresse'] = 'Adresse requise (5 à 200 caractères).'
    else:
        clean['adresse'] = adresse

    ville = str(data.get('ville') or '').strip()
    if ville not in CITIES:
        errors['ville'] = 'Sélectionnez une ville valide.'
    else:
        clean['ville'] = ville

    emplacement = str(data.get('emplacement') or '').strip()
    if emplacement not in {'Intérieur', 'Extérieur'}:
        errors['emplacement'] = 'Choisissez Intérieur ou Extérieur.'
    else:
        clean['emplacement'] = emplacement

    valeur_prix = str(data.get('prix') or '').strip()
    try:
        prix = Decimal(valeur_prix)
        if not prix.is_finite() or not (Decimal('0.01') <= prix <= Decimal('1000')) or prix.as_tuple().exponent < -2:
            raise ValueError()
        clean['prix'] = float(prix)
    except (InvalidOperation, ValueError):
        errors['prix'] = 'Prix entre 0,01 $ et 1 000 $, avec deux décimales maximum.'

    valeur_places = str(data.get('place') or '').strip()
    if not re.fullmatch(r'[0-9]{1,3}', valeur_places) or not 1 <= int(valeur_places) <= 100:
        errors['place'] = 'Entrez un nombre entier de places entre 1 et 100.'
    else:
        clean['place'] = int(valeur_places)

    dates = {}
    for field in ('dateDebut', 'dateFin'):
        s = str(data.get(field) or '').strip()
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', s):
                raise ValueError()
            dates[field] = datetime.strptime(s, '%Y-%m-%dT%H:%M')
        except ValueError:
            errors[field] = 'Entrez une date et une heure valides.'
    if len(dates) == 2:
        if dates['dateFin'] - dates['dateDebut'] < timedelta(minutes=30):
            errors['dateFin'] = 'La fin doit être au moins 30 minutes après le début.'
        else:
            clean['debut'] = dates['dateDebut'].strftime('%Y-%m-%d %H:%M')
            clean['fin'] = dates['dateFin'].strftime('%Y-%m-%d %H:%M')
    return clean, errors


def lire_photo(fichier, *, obligatoire=True):
    """Retourne (jpeg_bytes, erreur). Décode et réencode pour éliminer les contenus non-image."""
    if fichier is None or not fichier.filename:
        return None, ('Sélectionnez une photo.' if obligatoire else None)
    original = fichier.stream.read(MAX_PHOTO + 1)
    if len(original) > MAX_PHOTO:
        return None, 'Photo trop volumineuse (2 Mo maximum).'
    try:
        with Image.open(BytesIO(original)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                return None, 'Formats acceptés : JPEG, PNG, WebP.'
            source.verify()
        with Image.open(BytesIO(original)) as source:
            image = source.convert('RGB')
            image.thumbnail((1600, 1600))
            output = BytesIO()
            image.save(output, format='JPEG', quality=82, optimize=True)
            return output.getvalue(), None
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return None, 'Le fichier ne contient pas une image valide.'
