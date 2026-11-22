# Demo corpus fact ledger

All businesses and products below are fictional. Current facts are written in the Markdown pages and, where applicable, the PDFs. The three archived PDFs below deliberately preserve older statements; each is clearly marked as superseded.

## Current facts

| Fact | Statement | Source files |
|---|---|---|
| `address` | La boulangerie se trouve au 18 rue des Gras, 63000 Clermont-Ferrand. | `demo_site/access.md`, `demo_site/contact.md`, `demo_site/index.md`, `demo_site/pickup.md` |
| `phone` | Le téléphone de la boutique est le 04 73 00 12 34. | `demo_site/community.md`, `demo_site/contact.md` |
| `email` | L'adresse de contact est bonjour@trois-epis.example. | `demo_site/contact.md`, `demo_site/ordering.md`, `demo_site/privacy.md` |
| `hours_week` | Du mardi au vendredi, la boutique ouvre de 7 h à 19 h. | `demo_site/faq.md`, `demo_site/hours.md`, `demo_site/index.md` |
| `hours_sat` | Le samedi, la boutique ouvre de 7 h 30 à 18 h. | `demo_site/faq.md`, `demo_site/hours.md`, `demo_site/index.md` |
| `hours_sun` | Le dimanche, la boutique ouvre de 8 h à 12 h 30. | `demo_site/hours.md`, `demo_site/index.md` |
| `closed` | La boutique est fermée le lundi. | `demo_site/faq.md`, `demo_site/hours.md`, `demo_site/index.md` |
| `baguette` | La baguette tradition (250 g) coûte 1,30 €. | `demo_site/breads.md`, `demo_site/faq.md`, `demo_site/prices.md`, `demo_site/products/baguette.md`, `demo_site/tarifs.pdf` |
| `campagne` | Le pain de campagne (500 g) coûte 3,80 €. | `demo_site/breads.md`, `demo_site/prices.md`, `demo_site/tarifs.pdf` |
| `seigle` | Le pain de seigle (400 g) coûte 4,20 €. | `demo_site/breads.md` |
| `complet` | Le pain complet (500 g) coûte 3,60 €. | `demo_site/allergens.md`, `demo_site/breads.md` |
| `fougasse` | La fougasse aux olives coûte 4,50 € la pièce. | `demo_site/breads.md`, `demo_site/products/fougasse.md` |
| `croissant` | Le croissant pur beurre coûte 1,20 €. | `demo_site/prices.md`, `demo_site/tarifs.pdf`, `demo_site/viennoiseries.md` |
| `pain_choc` | Le pain au chocolat coûte 1,40 € depuis le 1er septembre 2026. | `demo_site/prices.md`, `demo_site/products/pain-au-chocolat.md`, `demo_site/tarifs.pdf`, `demo_site/viennoiseries.md` |
| `brioche` | La brioche nature (400 g) coûte 6,50 €. | `demo_site/viennoiseries.md` |
| `chausson` | Le chausson aux pommes coûte 2,20 €. | `demo_site/viennoiseries.md` |
| `cookie` | Le cookie chocolat-noisette coûte 2,00 €. | `demo_site/pastries.md`, `demo_site/prices.md`, `demo_site/tarifs.pdf` |
| `tarte` | La tarte aux pommes (6 parts) coûte 18 €. | `demo_site/cakes.md`, `demo_site/pastries.md`, `demo_site/prices.md`, `demo_site/tarifs.pdf` |
| `cake_order` | Les gâteaux personnalisés sont à commander au moins 48 heures à l'avance. | `demo_site/cakes.md`, `demo_site/ordering.md` |
| `cake_size` | Les gâteaux personnalisés sont proposés pour 6, 8 ou 10 personnes. | `demo_site/cakes.md` |
| `payment` | La boutique accepte les espèces, les cartes bancaires et les titres-restaurant papier. | `demo_site/faq.md`, `demo_site/payment.md` |
| `zone1` | La livraison couvre Clermont-Ferrand intra-muros pour 5 € par commande. | `demo_site/delivery.md`, `demo_site/delivery_zones.md`, `demo_site/livraison.pdf` |
| `zone2` | Chamalières et Beaumont sont desservis pour 7 € par commande. | `demo_site/delivery.md`, `demo_site/delivery_zones.md`, `demo_site/livraison.pdf` |
| `zone3` | Aubière et Royat sont desservis pour 9 € par commande. | `demo_site/delivery_zones.md` |
| `free_delivery` | La livraison est offerte dès 45 € d'achat dans toutes les zones desservies. | `demo_site/delivery.md`, `demo_site/delivery_zones.md`, `demo_site/faq.md`, `demo_site/livraison.pdf` |
| `delivery_min` | Le montant minimum d'une commande livrée est de 15 € avant frais de livraison. | `demo_site/delivery.md`, `demo_site/livraison.pdf`, `demo_site/ordering.md` |
| `delivery_window` | Les créneaux de livraison sont de 8 h à 10 h et de 14 h à 17 h, du mardi au samedi. | `demo_site/delivery.md`, `demo_site/livraison.pdf` |
| `delivery_cutoff` | Une commande en livraison doit être passée avant 16 h la veille. | `demo_site/delivery.md`, `demo_site/ordering.md` |
| `pickup` | Le retrait en boutique est gratuit et se fait aux horaires d'ouverture. | `demo_site/ordering.md`, `demo_site/pickup.md` |
| `custom_order` | Les commandes spéciales se réservent par téléphone ou par courriel. | `demo_site/events.md`, `demo_site/ordering.md`, `demo_site/terms.md` |
| `wheat_allergen` | La baguette tradition, le pain de campagne et le pain complet contiennent du gluten (blé). | `demo_site/allergenes.pdf`, `demo_site/allergens.md`, `demo_site/breads.md`, `demo_site/products/baguette.md` |
| `dairy_allergen` | Le croissant et la brioche contiennent du lait. | `demo_site/allergenes.pdf`, `demo_site/allergens.md`, `demo_site/products/pain-au-chocolat.md`, `demo_site/viennoiseries.md` |
| `nuts_allergen` | Le cookie chocolat-noisette contient des noisettes. | `demo_site/allergenes.pdf`, `demo_site/allergens.md`, `demo_site/pastries.md` |
| `cross_contact` | Les produits sont fabriqués dans un atelier qui manipule gluten, lait, œufs, fruits à coque et sésame; des traces croisées sont possibles. | `demo_site/allergenes.pdf`, `demo_site/allergens.md`, `demo_site/ingredients.md` |
| `returns` | Pour un produit non personnalisé, une réclamation est à signaler sous 14 jours après l'achat, avec le ticket. | `demo_site/cgv.pdf`, `demo_site/faq.md`, `demo_site/returns.md`, `demo_site/terms.md` |
| `perishable` | Les produits frais ou fabriqués sur commande ne sont ni repris ni échangés, sauf défaut constaté à la remise. | `demo_site/cgv.pdf`, `demo_site/retours.pdf`, `demo_site/returns.md`, `demo_site/terms.md` |
| `gift_card` | Les cartes cadeaux sont valables 12 mois à partir de leur date d'achat. | `demo_site/faq.md`, `demo_site/gift-cards.md` |
| `gift_amount` | Une carte cadeau peut être chargée de 10 €, 25 € ou 50 €. | `demo_site/gift-cards.md` |
| `workshop` | Un atelier de façonnage du pain est proposé le premier samedi du mois, de 14 h à 16 h. | `demo_site/events.md` |
| `workshop_price` | L'atelier de façonnage coûte 35 € par personne et accueille 6 personnes au maximum. | `demo_site/events.md` |
| `seasonal` | La galette des rois est proposée en janvier, en format 4 parts à 12 € et 6 parts à 17 €. | `demo_site/seasonal.md` |
| `bread_storage` | Le pain se conserve idéalement dans un sac en papier, à température ambiante, et se congèle tranché. | `demo_site/storage.md` |
| `ingredients` | Les pains courants sont pétris sur place avec farine, eau, levain ou levure et sel; les recettes détaillées sont disponibles en boutique. | `demo_site/about.md`, `demo_site/ingredients.md`, `demo_site/products/baguette.md`, `demo_site/products/fougasse.md` |
| `sourcing` | La farine de blé des pains courants provient d'un moulin situé dans le Puy-de-Dôme. | `demo_site/about.md`, `demo_site/sourcing.md` |
| `opening_order` | Les réservations de pains courants pour le lendemain sont acceptées jusqu'à 17 h par téléphone. | `demo_site/ordering.md`, `demo_site/pickup.md` |
| `complaint` | Pour une réclamation, écrivez à bonjour@trois-epis.example en indiquant la date d'achat et le produit concerné. | `demo_site/contact.md`, `demo_site/retours.pdf`, `demo_site/returns.md` |
| `access` | L'entrée de la boutique est de plain-pied; un arrêt de tram nommé Gaillard se trouve à environ 250 m. | `demo_site/access.md` |
| `community` | La boulangerie propose chaque mardi une miche de campagne à 3,50 € aux associations locales sur réservation. | `demo_site/community.md` |
| `privacy` | Les coordonnées communiquées pour une commande servent uniquement à son suivi et ne sont pas revendues. | `demo_site/privacy.md` |
| `cgv_payment` | Le paiement d'une commande spéciale est demandé au retrait; un acompte de 30 % est demandé pour les gâteaux personnalisés. | `demo_site/cakes.md`, `demo_site/cgv.pdf`, `demo_site/payment.md`, `demo_site/terms.md` |

## Deliberate superseded versions

| Fact | Older statement | Archived source | Current source |
|---|---|---|---|
| `pain_choc` | Ancien prix : 1,30 € jusqu'au 31 août 2026; remplacé par le tarif en vigueur du 1er septembre 2026. | `demo_site/tarifs.pdf` | `demo_site/prices.md`, `demo_site/products/pain-au-chocolat.md`, `demo_site/viennoiseries.md` |
| `zone1` | Ancien tarif Clermont-Ferrand : 4 € par commande jusqu'au 31 août 2026; remplacé par 5 € au 1er septembre 2026. | `demo_site/livraison.pdf` | `demo_site/delivery.md`, `demo_site/delivery_zones.md` |
| `returns` | Ancien délai de réclamation : 7 jours après achat jusqu'au 31 août 2026; remplacé par 14 jours au 1er septembre 2026. | `demo_site/retours.pdf` | `demo_site/cgv.pdf`, `demo_site/faq.md`, `demo_site/returns.md`, `demo_site/terms.md` |
