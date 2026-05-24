DEFAULT_TICKERS = [
    # ── NETHERLANDS (.AS) ──────────────────────────────────────
    "ASML.AS",   # ASML Holding
    "INGA.AS",   # ING Group
    "HEIA.AS",   # Heineken
    "UNA.AS",    # Unilever (NL listing)
    "ADYEN.AS",  # Adyen
    "ABN.AS",    # ABN AMRO
    "AGN.AS",    # Aegon
    "AD.AS",     # Ahold Delhaize
    "AKZA.AS",   # AkzoNobel
    "AALB.AS",   # Aalberts Industries
    "ASM.AS",    # ASM International
    "ASRNL.AS",  # ASR Nederland
    "BESI.AS",   # BE Semiconductor (Besi)
    "DSFIR.AS",  # DSM-Firmenich (post-2023 merger; old: DSM.AS)
    "IMCD.AS",   # IMCD Group
    "MT.AS",     # ArcelorMittal (NL listing)
    "NN.AS",     # NN Group
    "PHIA.AS",   # Philips
    "RAND.AS",   # Randstad
    "REN.AS",    # RELX (Amsterdam listing)
    "LIGHT.AS",  # Signify
    "UMG.AS",    # Universal Music Group
    "WKL.AS",    # Wolters Kluwer
    "URW.AS",    # Unibail-Rodamco-Westfield
    "KPN.AS",    # KPN
 
    # ── FRANCE (.PA) ──────────────────────────────────────────
    "MC.PA",     # LVMH
    "TTE.PA",    # TotalEnergies
    "OR.PA",     # L'Oréal
    "SAN.PA",    # Sanofi
    "AIR.PA",    # Airbus
    "BNP.PA",    # BNP Paribas
    "GLE.PA",    # Société Générale
    "RMS.PA",    # Hermès
    "KER.PA",    # Kering
    "CS.PA",     # AXA
    "RI.PA",     # Pernod Ricard
    "VIV.PA",    # Vivendi
    "PUB.PA",    # Publicis
    "ORAN.PA",   # Orange
    "BOL.PA",    # Bolloré
    "VIE.PA",    # Veolia (formerly VIE.PA)
    "DG.PA",     # Vinci
    "EI.PA",     # Eiffage  (was Eiff.PA in original — WRONG)
    "EN.PA",     # Bouygues  (was Bouy.PA in original — WRONG)
    "HO.PA",     # Thales
    "SAF.PA",    # Safran
    "MT.PA",     # ArcelorMittal (Paris listing; same stock as MT.AS)
    "URW.PA",    # Unibail-Rodamco-Westfield (Paris listing)
    "STLA.PA",   # Stellantis (Paris listing)
    "ICADE.PA",  # Icade REIT
    "GFC.PA",    # Gecina REIT  (GFC.PA appears correct)
    "KLE.PA",    # Klepierre REIT
    "COV.PA",    # Covivio REIT  (was CLI.PA in original — WRONG)
    "LI.PA",     # ⚠️ VERIFY — unclear what original intended
    "SBT.PA",    # ⚠️ VERIFY — unclear what original intended
    "VIN.PA",    # ⚠️ VERIFY — unclear what original intended
    "COFA.PA",   # Coface  (was COF.PA in original — WRONG)
 
    # ── GERMANY (.DE) ─────────────────────────────────────────
    "SAP.DE",    # SAP
    "SIE.DE",    # Siemens
    "DTE.DE",    # Deutsche Telekom
    "BMW.DE",    # BMW
    "MBG.DE",    # Mercedes-Benz Group  (Daimler renamed 2021)
    "VOW3.DE",   # Volkswagen (preferred)
    "BAS.DE",    # BASF
    "BAYN.DE",   # Bayer
    "ALV.DE",    # Allianz
    "MUV2.DE",   # Munich Re
    "DBK.DE",    # Deutsche Bank
    "CBK.DE",    # Commerzbank
    "DHL.DE",    # Deutsche Post / DHL Group
    "HEI.DE",    # HeidelbergCement (renamed Heidelberg Materials)
    "RWE.DE",    # RWE
    "EOAN.DE",   # E.ON
    "ENR.DE",    # Siemens Energy
    "TKA.DE",    # thyssenkrupp
    "ADS.DE",    # Adidas  (was Adidas.DE — WRONG)
    "BEI.DE",    # Beiersdorf  (was Beiersdorf.DE — WRONG)
    "BNR.DE",    # Brenntag  (was Brenntag.DE — WRONG)
    "CON.DE",    # Continental  (was Continental.DE — WRONG)
    "EVK.DE",    # Evonik  (was Evonik.DE — WRONG)
    "FRE.DE",    # Fresenius  (was Fresenius.DE — WRONG)
    "HNR1.DE",   # Hannover Rück  (was Hannover.DE — WRONG)
    "HBCG.DE",   # Heidelberg Materials  (was Heidelberg.DE — WRONG)
    "HEN3.DE",   # Henkel preference  (was Henkel.DE — WRONG)
    "IFX.DE",    # Infineon  (was Infineon.DE — WRONG)
    "KBX.DE",    # Knorr-Bremse  (was Knorr.DE — WRONG)
    "LEG.DE",    # LEG Immobilien
    "MRK.DE",    # Merck KGaA  (was Merck.DE — WRONG; NB: different from US Merck)
    "MTX.DE",    # MTU Aero Engines  (was MTU.DE — WRONG)
    "P911.DE",   # Porsche AG  (was Porsche.DE — WRONG)
    "PUM.DE",    # Puma  (was Puma.DE — WRONG)
    "QIA.DE",    # QIAGEN  (was Qiagen.DE — WRONG)
    "RHM.DE",    # Rheinmetall  (was Rheinmetall.DE — WRONG)
    "SRT3.DE",   # Sartorius preference  (was Sartorius.DE — WRONG)
    "SY1.DE",    # Symrise  (was Symrise.DE — WRONG)
    "VNA.DE",    # Vonovia  (was Vonovia.DE — WRONG)
    "ZAL.DE",    # Zalando  (was Zalando.DE — WRONG)
    "DTG.DE",    # Daimler Truck (split from MBG in 2021)
    # "1COV.DE", # Covestro — acquired by ADNOC Oct 2024, likely DELISTED
    # SZG.DE is Salzgitter — keeping if valid
 
    # ── UK (.L) ───────────────────────────────────────────────
    "SHEL.L",    # Shell
    "AZN.L",     # AstraZeneca
    "HSBA.L",    # HSBC
    "BP.L",      # BP
    "GSK.L",     # GSK
    "ULVR.L",    # Unilever (UK listing)
    "DGE.L",     # Diageo
    "RIO.L",     # Rio Tinto
    "GLEN.L",    # Glencore
    "BHP.L",     # BHP (London listing)
    "ANTO.L",    # Antofagasta
    "AAL.L",     # Anglo American
    "BARC.L",    # Barclays
    "LLOY.L",    # Lloyds Banking Group
    "NWG.L",     # NatWest Group
    "STAN.L",    # Standard Chartered
    "PRU.L",     # Prudential
    "AV.L",      # Aviva
    "LGEN.L",    # Legal & General
    "ABF.L",     # Associated British Foods
    "REL.L",     # RELX (London listing)
    "WPP.L",     # WPP
    "VOD.L",     # Vodafone
    "BT-A.L",    # BT Group
    "MNDI.L",    # Mondi
    "SMDS.L",    # DS Smith
    "SKG.L",     # Smurfit Kappa
    "HLN.L",     # Haleon
    "SN.L",      # Smith & Nephew
    "SGE.L",     # Sage Group
    "INF.L",     # Informa
    "EXPN.L",    # Experian
    "SGRO.L",    # Segro REIT
    "LAND.L",    # Land Securities REIT
    "BLND.L",    # British Land REIT
    "PHP.L",     # Primary Health Properties REIT
    "BBOX.L",    # Tritax Big Box REIT
    "ITV.L",     # ITV
    "CRH.L",     # CRH
    "DCC.L",     # DCC
    "IAG.L",     # IAG (Int'l Airlines Group; also IAG.MC)
    "BDEV.L",    # Barratt Developments  (was Barratt.L — WRONG)
    "BATS.L",    # British American Tobacco  (was British.L — WRONG/AMBIGUOUS)
    "BNZL.L",    # Bunzl  (was Bunzl.L — WRONG)
    "BRBY.L",    # Burberry  (was Burberry.L — WRONG)
    "CPG.L",     # Compass Group  (was Compass.L — WRONG)
    "ENT.L",     # Entain  (was Entain.L — WRONG)
    "FLTR.L",    # Flutter Entertainment  (was Flutter.L — WRONG)
    "HLMA.L",    # Halma  (was Halma.L — WRONG)
    "HL.L",      # Hargreaves Lansdown  (was Hargreaves.L — WRONG)
    "IMB.L",     # Imperial Brands  (was Imperial.L — WRONG)
    "IHG.L",     # InterContinental Hotels  (was InterContinental.L — WRONG)
    "ITRK.L",    # Intertek  (was Intertek.L — WRONG)
    "KGF.L",     # Kingfisher  (was Kingfisher.L — WRONG)
    "LSEG.L",    # London Stock Exchange Group  (was London.L — WRONG)
    "MNG.L",     # M&G  (was M&G.L — WRONG)
    "MRO.L",     # Melrose Industries  (was Melrose.L — WRONG)
    "NG.L",      # National Grid  (was National.L — WRONG)
    "NXT.L",     # Next  (was Next.L — WRONG)
    "OCDO.L",    # Ocado  (was Ocado.L — WRONG)
    "PSON.L",    # Pearson  (was Pearson.L — WRONG)
    "PSN.L",     # Persimmon  (was Persimmon.L — WRONG)
    "PHNX.L",    # Phoenix Group  (was Phoenix.L — WRONG)
    "RKT.L",     # Reckitt Benckiser  (was Reckitt.L — WRONG)
    "RTO.L",     # Rentokil  (was Rentokil.L — WRONG)
    "RMV.L",     # Rightmove  (was Rightmove.L — WRONG)
    "RR.L",      # Rolls-Royce  (was Rolls.L — WRONG)
    "SBRY.L",    # Sainsbury's  (was Sainsbury.L — WRONG)
    "SDR.L",     # Schroders  (was Schroders.L — WRONG)
    "SVT.L",     # Severn Trent  (was Severn.L — WRONG)
    "SMIN.L",    # Smiths Group  (was Smiths.L — WRONG)
    "SPX.L",     # Spirax-Sarco  (was Spirax.L — WRONG)
    "SSE.L",     # SSE
    "TW.L",      # Taylor Wimpey  (was Taylor.L — WRONG)
    "TSCO.L",    # Tesco  (was Tesco.L — WRONG)
    "WEIR.L",    # Weir Group  (was Weir.L — WRONG)
    "WTB.L",     # Whitbread  (was Whitbread.L — WRONG)
    "AAF.L",     # Airtel Africa  (was Airtel.L — WRONG)
    "BEZ.L",     # Beazley  (was Beazley.L — WRONG)
    "CNA.L",     # Centrica  (was Centrica.L — WRONG)
    "CTEC.L",    # ConvaTec  (was ConvaTec.L — WRONG)
    "FCIT.L",    # F&C Investment Trust  (was F&C.L — WRONG)
    "FRAS.L",    # Frasers Group  (was Frasers.L — WRONG)
    "HBR.L",     # Harbour Energy  (was Harbour.L — WRONG)
    "HIK.L",     # Hikma Pharmaceuticals  (was Hikma.L — WRONG)
    "HWDN.L",    # Howden Joinery  (was Howden.L — WRONG)
    "INVP.L",    # Investec  (was Investec.L — WRONG)
    "JMAT.L",    # Johnson Matthey  (was Johnson.L — WRONG/AMBIGUOUS)
    "MKS.L",     # Marks & Spencer  (was Marks.L — WRONG)
    "MAB.L",     # Mitchells & Butlers  (was Mitchells.L — WRONG)
    "PNN.L",     # Pennon Group  (was Pennon.L — WRONG)
    "PETS.L",    # Pets at Home
    "QLT.L",     # Quilter  (was Quilter.L — WRONG)
    "REDD.L",    # Redde Northgate  (was Redde.L — WRONG)
    "ROR.L",     # Rotork  (was Rotork.L — WRONG)
    "SVS.L",     # Savills  (was Savills.L — WRONG)
    "SRP.L",     # Serco  (was Serco.L — WRONG)
    "SXS.L",     # Spectris  (was Spectris.L — WRONG)
    "SPT.L",     # Spirent Communications  (was Spirent.L — WRONG)
    "TATE.L",    # Tate & Lyle
    "TPK.L",     # Travis Perkins  (was Travis.L — WRONG)
    "VSVS.L",    # Vesuvius  (was Vesuvius.L — WRONG)
    "VCT.L",     # Victrex  (was Victrex.L — WRONG)
    "VTY.L",     # Vistry Group  (was Vistry.L — WRONG)
    "WIZZ.L",    # Wizz Air
    "WG.L",      # John Wood Group  (was Wood.L — WRONG)
    "WKP.L",     # Workspace Group  (was Workspace.L — WRONG)
    "HMSO.L",    # Hammerson REIT
    "UTG.L",     # Unite Group REIT
    "BYG.L",     # Big Yellow Group REIT
    "EMIS.L",    # EMIS Group  (⚠️ verify — may have been acquired)
 
    # Irish stocks — primary Dublin, secondary London listing
    "RYA.IR",    # Ryanair (primary Dublin)
    "RYA.L",     # Ryanair (London secondary)
    "KYGA.IR",   # Kerry Group (primary Dublin)
    "SKG.IR",    # Smurfit Kappa (primary Dublin; SKG.L also exists)
    "KRX.IR",    # Kingspan Group (primary Dublin)
    "AIBG.IR",   # AIB Group (primary Dublin)
    "BIRG.IR",   # Bank of Ireland (primary Dublin)
    "GLB.IR",    # Glanbia (primary Dublin)
 
    # ── SWITZERLAND (.SW) ─────────────────────────────────────
    "NESN.SW",   # Nestlé
    "NOVN.SW",   # Novartis
    "ROG.SW",    # Roche
    "UBSG.SW",   # UBS Group
    "ABBN.SW",   # ABB  (was ABB.SW — WRONG)
    "ZURN.SW",   # Zurich Insurance  (was Zurich.SW — WRONG)
    "SREN.SW",   # Swiss Re  (was SwissRe.SW — WRONG)
    "BALN.SW",   # Baloise  (was Baloise.SW — WRONG)
    "LONN.SW",   # Lonza  (was Lonza.SW — WRONG)
    "ALC.SW",    # Alcon  (was Alcon.SW — WRONG)
    "ADEN.SW",   # Adecco  (was Adecco.SW — WRONG)
    "CLN.SW",    # Clariant  (was Clariant.SW — WRONG)
    "EMSN.SW",   # EMS-Chemie  (was EMS.SW — WRONG)
    "GEBN.SW",   # Geberit  (was Geberit.SW — WRONG)
    "GIVN.SW",   # Givaudan  (was Givaudan.SW — WRONG)
    "HELN.SW",   # Helvetia  (was Helvetia.SW — WRONG)
    "HOLN.SW",   # Holcim  (was Holcim.SW — WRONG)
    "JUBN.SW",   # Julius Baer  (was Julius.SW — WRONG)
    "KNIN.SW",   # Kuehne + Nagel  (was Kuehne.SW — WRONG)
    "LISP.SW",   # Lindt & Sprüngli PC  (was Lindt.SW — WRONG)
    "LOGN.SW",   # Logitech  (was Logitech.SW — WRONG)
    "PGHN.SW",   # Partners Group  (was PSI.SW — WRONG)
    "CFR.SW",    # Richemont  (was Richemont.SW — WRONG)
    "SCHN.SW",   # Schindler  (was Schindler.SW — WRONG)
    "SGSN.SW",   # SGS  (was SGS.SW — WRONG)
    "SIKA.SW",   # Sika
    "SOON.SW",   # Sonova  (was Sonova.SW — WRONG)
    "STMN.SW",   # Straumann  (was Straumann.SW — WRONG)
    "UHR.SW",    # Swatch Group  (was Swatch.SW — WRONG)
    "SCMN.SW",   # Swisscom  (was Swisscom.SW — WRONG)
    "TEMN.SW",   # Temenos  (was Temenos.SW — WRONG)
    "VONN.SW",   # Vontobel  (was Vontobel.SW — WRONG)
 
    # ── ITALY (.MI) ───────────────────────────────────────────
    "ENEL.MI",   # Enel
    "ENI.MI",    # Eni
    "UCG.MI",    # UniCredit
    "ISP.MI",    # Intesa Sanpaolo
    "RACE.MI",   # Ferrari (Milan listing)
    "STLA.MI",   # Stellantis (Milan listing)
    "G.MI",      # Generali Assicurazioni
    "ASS.MI",    # Assicurazioni Generali (⚠️ same as G.MI — verify)
    "SNAM.MI",   # Snam
    "TRN.MI",    # Terna
    "A2A.MI",    # A2A
    "ERG.MI",    # ERG
    "MONC.MI",   # Moncler
    "PRY.MI",    # Prysmian
    "BAMI.MI",   # Banco BPM
    "BPER.MI",   # BPER Banca
    "PST.MI",    # Poste Italiane  (POST.MI in original was WRONG — PST.MI is correct)
    "HER.MI",    # Hera
    "EXO.MI",    # Exor NV (Agnelli holding)
    "IRE.MI",    # IREN SpA
    "IGD.MI",    # IGD SIIQ REIT
    "SRG.MI",    # Saipem (⚠️ SRG.MI was Snam subsidiary; verify)
    "FBK.MI",    # FinecoBank
 
    # ── SPAIN (.MC) ───────────────────────────────────────────
    "SAN.MC",    # Santander
    "BBVA.MC",   # BBVA
    "IBE.MC",    # Iberdrola
    "ITX.MC",    # Inditex  (was Inditex.MC — WRONG)
    "REP.MC",    # Repsol
    "TEF.MC",    # Telefónica
    "AMS.MC",    # Amadeus IT  (was Amadeus.MC — WRONG)
    "ANA.MC",    # Acciona  (was Acciona.MC — WRONG)
    "ACX.MC",    # Acerinox  (was Acerinox.MC — WRONG)
    "AENA.MC",   # Aena  (was Aena.MC — WRONG)
    "BKT.MC",    # Bankinter  (was Bankinter.MC — WRONG)
    "CABK.MC",   # CaixaBank  (was Caixa.MC — WRONG)
    "CLNX.MC",   # Cellnex  (was Cellnex.MC — WRONG)
    "ENG.MC",    # Enagás  (was Enagas.MC — WRONG)
    "ELE.MC",    # Endesa  (was Endesa.MC — WRONG)
    "FER.MC",    # Ferrovial
    "GRF.MC",    # Grifols  (was Grifols.MC — WRONG)
    "IAG.MC",    # IAG (also IAG.L)
    "IDR.MC",    # Indra  (was Indra.MC — WRONG)
    "MAP.MC",    # Mapfre
    "MEL.MC",    # Meliá Hotels  (was Melia.MC — WRONG)
    "MRL.MC",    # Merlin Properties REIT  (was Merlin.MC — WRONG)
    "NTGY.MC",   # Naturgy  (was Naturgy.MC — WRONG)
    "REE.MC",    # Red Eléctrica (REE)  (was Red.MC — WRONG)
    "SAB.MC",    # Banco Sabadell  (was Sabadell.MC — WRONG)
    "SLR.MC",    # Solaria  (was Solaria.MC — WRONG)
    "ACS.MC",    # ACS Group
    "FCC.MC",    # FCC
    "COL.MC",    # ⚠️ VERIFY — unclear; Colt Group? ColGroup?
    "MERL.MC",   # ⚠️ VERIFY — possibly wrong; Merlin is MRL.MC
 
    # ── BELGIUM (.BR) ─────────────────────────────────────────
    "KBC.BR",    # KBC Group
    "COLR.BR",   # Colruyt
    "PROX.BR",   # Proximus
    "UCB.BR",    # UCB
    "SOLB.BR",   # Solvay
    "ARGX.BR",   # argenx
    "WDP.BR",    # WDP (Warehouses De Pauw) REIT
    "BEKB.BR",   # Bekaert
    "ACKB.BR",   # Ackermans & van Haaren  (was Ackermans.BR — WRONG)
    "SOF.BR",    # Sofina  (was Sofina.BR — WRONG)
    "AGS.BR",    # Ageas  (was Ageas.BR — WRONG)
    "MELE.BR",   # Melexis  (was Melexis.BR — WRONG)
    "ELI.BR",    # Elia Group  (was Elia.BR — WRONG)
    "TNET.BR",   # Telenet  (was Telenet.BR — WRONG)
    "LOTB.BR",   # Lotus Bakeries  (was Lotus.BR — WRONG)
    "DETE.BR",   # D'Ieteren Group  (was Deteren.BR — WRONG)
    "AEDIF.BR",  # Aedifica REIT  (was Aedificia.BR — WRONG)
    "GBL.BR",    # Groupe Bruxelles Lambert
    "UMI.BR",    # Umicore
    "XIOR.BR",   # Xior Student Housing REIT
    "VGP.BR",    # VGP NV REIT
    "COFB.BR",   # Cofinimmo REIT
    "AED.BR",    # ⚠️ VERIFY — possibly AEDIF.BR duplicate
 
    # ── FINLAND (.HE) ─────────────────────────────────────────
    "NESTE.HE",  # Neste  (was Neste.HE — wrong case)
    "NOKIA.HE",  # Nokia  (was Nokia.HE — wrong case)
    "SAMPO.HE",  # Sampo  (was Sampo.HE — wrong case)
    "STERV.HE",  # Stora Enso  (was Stora.HE — WRONG)
    "UPM.HE",    # UPM-Kymmene
    "OUT1V.HE",  # Outokumpu
    "ELISA.HE",  # Elisa  (was Elisa.HE — wrong case)
    "NOKIA.HE",  # Nokia
    "KNEBV.HE",  # Kone  (was Kone.HE — WRONG)
    "KCR.HE",    # Konecranes  (was Konecranes.HE — WRONG)
    "METSO.HE",  # Metso  (was Metso.HE — WRONG)
    "VALMT.HE",  # Valmet  (was Valmet.HE — WRONG)
    "WRT1V.HE",  # Wärtsilä  (was Wartsila.HE — WRONG)
    "HUH1V.HE",  # Huhtamäki  (was Huhtamaki.HE — WRONG)
    "KEMIRA.HE", # Kemira  (was Kemira.HE — wrong case)
    "ORNBV.HE",  # Orion  (was Orion.HE — WRONG)
    "NRE1V.HE",  # Nokian Tyres  (was Nokian.HE — WRONG)
    "YIT.HE",    # YIT Corporation
    "CGCBV.HE",  # Cargotec  (was Cargotec.HE — WRONG; note: split into Kalmar/Hiab 2023)
    "TELA1.HE",  # ⚠️ VERIFY
    "METSB.HE",  # ⚠️ VERIFY (Metso B shares?)
    "KESKOB.HE", # Kesko B
 
    # ── SWEDEN (.ST) ──────────────────────────────────────────
    "VOLV-B.ST", # Volvo B
    "SAND.ST",   # Sandvik
    "SKF-B.ST",  # SKF B
    "ALFA.ST",   # Alfa Laval
    "ATCO-A.ST", # Atlas Copco A
    "ATCO-B.ST", # Atlas Copco B
    "EPI-A.ST",  # Epiroc A
    "EPI-B.ST",  # Epiroc B
    "HEXA-B.ST", # Hexagon B
    "ASSA-B.ST", # ASSA ABLOY B
    "NIBE-B.ST", # NIBE B
    "LIFCO-B.ST",# Lifco B
    "TEL2-B.ST", # Tele2 B
    "SSAB-B.ST", # SSAB B
    "BOL.ST",    # Boliden
    "ICA.ST",    # ICA Gruppen
    "TELIA.ST",  # Telia Company  (was Telia.ST — wrong code)
    "EVO.ST",    # Evolution Gaming  (was Evolution.ST — WRONG)
    "ERIC-B.ST", # Ericsson B  (was Ericsson.ST — WRONG)
    "ELUX-B.ST", # Electrolux B  (was Electrolux.ST — WRONG)
    "ESSITY-B.ST",# Essity B  (was Essity.ST — WRONG)
    "GETI-B.ST", # Getinge B  (was Getinge.ST — WRONG)
    "HM-B.ST",   # H&M B  (was Hennes.ST — WRONG)
    "HOLMB.ST",  # Holmen B  (was Holmen.ST — WRONG)
    "HUSQ-B.ST", # Husqvarna B  (was Husqvarna.ST — WRONG)
    "INDU-A.ST", # Industrivärden A  (was Industrivarden.ST — WRONG)
    "INVE-B.ST", # Investor B  (was Investor.ST — WRONG)
    "KINV-B.ST", # Kinnevik B  (was Kinnevik.ST — WRONG)
    "LUND-B.ST", # Lundbergföretagen B  (was Lundberg.ST — WRONG)
    "SAAB-B.ST", # Saab B  (was Saab.ST — WRONG)
    "SCA-B.ST",  # SCA B  (was SCA.ST — WRONG)
    "SEB-A.ST",  # SEB A  (was SEB.ST — WRONG)
    "SECU-B.ST", # Securitas B  (was Securitas.ST — WRONG)
    "SKA-B.ST",  # Skanska B  (was Skanska.ST — WRONG)
    "SWED-A.ST", # Swedbank A  (was Svenska.ST — WRONG)
    # "SCAB.ST",  # ⚠️ UNKNOWN — remove
    # "INDT.ST",  # ⚠️ UNKNOWN — remove
    # "ADDB.ST",  # ⚠️ UNKNOWN — Addtech is ADDT-B.ST
    # "NLR.ST",   # ⚠️ UNKNOWN — remove
 
    # ── NORWAY (.OL) ──────────────────────────────────────────
    "EQNR.OL",   # Equinor  (was Equinor.OL — WRONG)
    "DNB.OL",    # DNB Bank
    "AKERBP.OL", # Aker BP
    "AKER.OL",   # Aker ASA  (was Aker.OL — wrong case)
    "MOWI.OL",   # Mowi (salmon farming)  (was Mowi.OL — wrong case)
    "TEL.OL",    # Telenor  (was Telenor.OL — WRONG)
    "YAR.OL",    # Yara International  (was Yara.OL — WRONG)
    "ORK.OL",    # Orkla  (was Orkla.OL — WRONG)
    "STB.OL",    # Storebrand  (was Storebrand.OL — WRONG)
    "NHY.OL",    # Norsk Hydro  (was Norsk.OL — WRONG)
    "SALM.OL",   # SalMar  (was Salmar.OL — WRONG)
    "SCHA.OL",   # Schibsted A  (was Schibsted.OL — WRONG)
    "SUBC.OL",   # Subsea 7  (was Subsea.OL — WRONG)
    "GJF.OL",    # Gjensidige  (was Gensidige.OL — WRONG + MISSPELLED)
    "VAR.OL",    # Vår Energi
 
    # ── DENMARK (.CO) ─────────────────────────────────────────
    "DSV.CO",    # DSV (logistics)
    "MAERSK-B.CO",# A.P. Møller-Mærsk B
    "NOVO-B.CO", # Novo Nordisk B  (was Novo.CO — WRONG)
    "NZYM-B.CO", # Novozymes B  (was Novozymes.CO — WRONG)
    "CARL-B.CO", # Carlsberg B  (was Carlsberg.CO — WRONG)
    "COLO-B.CO", # Coloplast B  (was Coloplast.CO — WRONG)
    "DEMANT.CO", # Demant (hearing)  (was Demant.CO — verify case)
    "FLS.CO",    # FLSmidth  (was Flsmidth.CO — WRONG)
    "GMAB.CO",   # Genmab  (was Genmab.CO — WRONG)
    "GN.CO",     # GN Audio
    "ISS.CO",    # ISS A/S  (was Iss.CO — wrong case)
    "JYSK.CO",   # Jyske Bank  (was Jyske.CO — WRONG)
    "NKT.CO",    # NKT  (was Nkt.CO — wrong case)
    "ORSTED.CO", # Ørsted  (was Orsted.CO — verify case)
    "PNDORA.CO", # Pandora  (was Pandora.CO — WRONG)
    "ROCK-B.CO", # Rockwool B  (was Rockwool.CO — WRONG)
    "RBREW.CO",  # Royal Unibrew  (was Royal.CO — WRONG)
    # "SIM.CO",  # Simcorp — acquired by Deutsche Börse 2023, DELISTED
    "SPAR.CO",   # Spar Nord Bank  (was Spar.CO — verify case)
    "SYDB.CO",   # Sydbank  (was Sydbank.CO — WRONG)
    "TOP.CO",    # Topdanmark  (was Topdanmark.CO — WRONG)
    "TRYG.CO",   # Tryg
    "VWS.CO",    # Vestas  (was Vestas.CO — WRONG)
    "ZEAL.CO",   # Zealand Pharma  (was Zealand.CO — WRONG)
    "AMBU-B.CO", # Ambu B  (was Ambu.CO — WRONG)
    # "WILLIAM.CO", # ⚠️ UNCLEAR — remove (William Demant = Demant = DEMANT.CO)
 
    # ── PORTUGAL (.LS) ────────────────────────────────────────
    "GALP.LS",   # Galp Energia
    "EDP.LS",    # EDP - Energias de Portugal
    "EDPR.LS",   # EDP Renováveis
    "BCP.LS",    # Banco Comercial Português
    "JMT.LS",    # Jerónimo Martins  (was Jeronimo.LS — WRONG)
    "NVG.LS",    # The Navigator Company  (was Navigator.LS — WRONG)
    "RENE.LS",   # REN  (was REN.LS — WRONG)
    "SON.LS",    # Sonae  (was Sonae.LS — WRONG)
    "NOS.LS",    # NOS
    "ALTRI.LS",  # Altri  (was Altri.LS — wrong case)
 
    # ── AUSTRIA (.VI) ─────────────────────────────────────────
    "OMV.VI",    # OMV
    "WIE.VI",    # Wienerberger
    "VOEST.VI",  # voestalpine
    "ANDR.VI",   # Andritz
    "EBS.VI",    # Erste Group Bank
    "RBI.VI",    # Raiffeisen Bank International
    "VIG.VI",    # Vienna Insurance Group

    # USA
    "MMM",
    "AOS",
    "ABT",
    "ABBV",
    "ACN",
    "ADBE",
    "AMD",
    "AES",
    "AFL",
    "A",
    "APD",
    "ABNB",
    "AKAM",
    "ALB",
    "ARE",
    "ALGN",
    "ALLE",
    "LNT",
    "ALL",
    "GOOGL",
    "GOOG",
    "MO",
    "AMZN",
    "AMCR",
    "AEE",
    "AEP",
    "AXP",
    "AIG",
    "AMT",
    "AWK",
    "AMP",
    "AME",
    "AMGN",
    "APH",
    "ADI",
    "AON",
    "APA",
    "APO",
    "AAPL",
    "AMAT",
    "APP",
    "APTV",
    "ACGL",
    "ADM",
    "ARES",
    "ANET",
    "AJG",
    "AIZ",
    "T",
    "ATO",
    "ADSK",
    "ADP",
    "AZO",
    "AVB",
    "AVY",
    "AXON",
    "BKR",
    "BALL",
    "BAC",
    "BAX",
    "BDX",
    "BRK-B",
    "BBY",
    "TECH",
    "BIIB",
    "BLK",
    "BX",
    "XYZ",
    "BNY",
    "BA",
    "BKNG",
    "BSX",
    "BMY",
    "AVGO",
    "BR",
    "BRO",
    "BF-B",
    "BLDR",
    "BG",
    "BXP",
    "CHRW",
    "CDNS",
    "CPT",
    "CPB",
    "COF",
    "CAH",
    "CCL",
    "CARR",
    "CVNA",
    "CASY",
    "CAT",
    "CBOE",
    "CBRE",
    "CDW",
    "COR",
    "CNC",
    "CNP",
    "CF",
    "CRL",
    "SCHW",
    "CHTR",
    "CVX",
    "CMG",
    "CB",
    "CHD",
    "CIEN",
    "CI",
    "CINF",
    "CTAS",
    "CSCO",
    "C",
    "CFG",
    "CLX",
    "CME",
    "CMS",
    "KO",
    "CTSH",
    "COHR",
    "COIN",
    "CL",
    "CMCSA",
    "FIX",
    "CAG",
    "COP",
    "ED",
    "STZ",
    "CEG",
    "COO",
    "CPRT",
    "GLW",
    "CPAY",
    "CTVA",
    "CSGP",
    "COST",
    "CRH",
    "CRWD",
    "CCI",
    "CSX",
    "CMI",
    "CVS",
    "DHR",
    "DRI",
    "DDOG",
    "DVA",
    "DECK",
    "DE",
    "DELL",
    "DAL",
    "DVN",
    "DXCM",
    "FANG",
    "DLR",
    "DG",
    "DLTR",
    "D",
    "DPZ",
    "DASH",
    "DOV",
    "DOW",
    "DHI",
    "DTE",
    "DUK",
    "DD",
    "ETN",
    "EBAY",
    "SATS",
    "ECL",
    "EIX",
    "EW",
    "EA",
    "ELV",
    "EME",
    "EMR",
    "ETR",
    "EOG",
    "EPAM",
    "EQT",
    "EFX",
    "EQIX",
    "EQR",
    "ERIE",
    "ESS",
    "EL",
    "EG",
    "EVRG",
    "ES",
    "EXC",
    "EXE",
    "EXPE",
    "EXPD",
    "EXR",
    "XOM",
    "FFIV",
    "FDS",
    "FICO",
    "FAST",
    "FRT",
    "FDX",
    "FIS",
    "FITB",
    "FSLR",
    "FE",
    "FISV",
    "F",
    "FTNT",
    "FTV",
    "FOXA",
    "FOX",
    "BEN",
    "FCX",
    "GRMN",
    "IT",
    "GE",
    "GEHC",
    "GEV",
    "GEN",
    "GNRC",
    "GD",
    "GIS",
    "GM",
    "GPC",
    "GILD",
    "GPN",
    "GL",
    "GDDY",
    "GS",
    "HAL",
    "HIG",
    "HAS",
    "HCA",
    "DOC",
    "HSIC",
    "HSY",
    "HPE",
    "HLT",
    "HD",
    "HON",
    "HRL",
    "HST",
    "HWM",
    "HPQ",
    "HUBB",
    "HUM",
    "HBAN",
    "HII",
    "IBM",
    "IEX",
    "IDXX",
    "ITW",
    "INCY",
    "IR",
    "PODD",
    "INTC",
    "IBKR",
    "ICE",
    "IFF",
    "IP",
    "INTU",
    "ISRG",
    "IVZ",
    "INVH",
    "IQV",
    "IRM",
    "JBHT",
    "JBL",
    "JKHY",
    "J",
    "JNJ",
    "JCI",
    "JPM",
    "KVUE",
    "KDP",
    "KEY",
    "KEYS",
    "KMB",
    "KIM",
    "KMI",
    "KKR",
    "KLAC",
    "KHC",
    "KR",
    "LHX",
    "LH",
    "LRCX",
    "LVS",
    "LDOS",
    "LEN",
    "LII",
    "LLY",
    "LIN",
    "LYV",
    "LMT",
    "L",
    "LOW",
    "LULU",
    "LITE",
    "LYB",
    "MTB",
    "MPC",
    "MAR",
    "MRSH",
    "MLM",
    "MAS",
    "MA",
    "MKC",
    "MCD",
    "MCK",
    "MDT",
    "MRK",
    "META",
    "MET",
    "MTD",
    "MGM",
    "MCHP",
    "MU",
    "MSFT",
    "MAA",
    "MRNA",
    "TAP",
    "MDLZ",
    "MPWR",
    "MNST",
    "MCO",
    "MS",
    "MOS",
    "MSI",
    "MSCI",
    "NDAQ",
    "NTAP",
    "NFLX",
    "NEM",
    "NWSA",
    "NWS",
    "NEE",
    "NKE",
    "NI",
    "NDSN",
    "NSC",
    "NTRS",
    "NOC",
    "NCLH",
    "NRG",
    "NUE",
    "NVDA",
    "NVR",
    "NXPI",
    "ORLY",
    "OXY",
    "ODFL",
    "OMC",
    "ON",
    "OKE",
    "ORCL",
    "OTIS",
    "PCAR",
    "PKG",
    "PLTR",
    "PANW",
    "PSKY",
    "PH",
    "PAYX",
    "PYPL",
    "PNR",
    "PEP",
    "PFE",
    "PCG",
    "PM",
    "PSX",
    "PNW",
    "PNC",
    "POOL",
    "PPG",
    "PPL",
    "PFG",
    "PG",
    "PGR",
    "PLD",
    "PRU",
    "PEG",
    "PTC",
    "PSA",
    "PHM",
    "PWR",
    "QCOM",
    "DGX",
    "RL",
    "RJF",
    "RTX",
    "O",
    "REG",
    "REGN",
    "RF",
    "RSG",
    "RMD",
    "RVTY",
    "HOOD",
    "ROK",
    "ROL",
    "ROP",
    "ROST",
    "RCL",
    "SPGI",
    "CRM",
    "SNDK",
    "SBAC",
    "SLB",
    "STX",
    "SRE",
    "NOW",
    "SHW",
    "SPG",
    "SWKS",
    "SJM",
    "SW",
    "SNA",
    "SOLV",
    "SO",
    "LUV",
    "SWK",
    "SBUX",
    "STT",
    "STLD",
    "STE",
    "SYK",
    "SMCI",
    "SYF",
    "SNPS",
    "SYY",
    "TMUS",
    "TROW",
    "TTWO",
    "TPR",
    "TRGP",
    "TGT",
    "TEL",
    "TDY",
    "TER",
    "TSLA",
    "TXN",
    "TPL",
    "TXT",
    "TMO",
    "TJX",
    "TKO",
    "TTD",
    "TSCO",
    "TT",
    "TDG",
    "TRV",
    "TRMB",
    "TFC",
    "TYL",
    "TSN",
    "USB",
    "UBER",
    "UDR",
    "ULTA",
    "UNP",
    "UAL",
    "UPS",
    "URI",
    "UNH",
    "UHS",
    "VLO",
    "VEEV",
    "VTR",
    "VLTO",
    "VRSN",
    "VRSK",
    "VZ",
    "VRTX",
    "VRT",
    "VTRS",
    "VICI",
    "V",
    "VST",
    "VMC",
    "WRB",
    "GWW",
    "WAB",
    "WMT",
    "DIS",
    "WBD",
    "WM",
    "WAT",
    "WEC",
    "WFC",
    "WELL",
    "WST",
    "WDC",
    "WY",
    "WSM",
    "WMB",
    "WTW",
    "WDAY",
    "WYNN",
    "XEL",
    "XYL",
    "YUM",
    "ZBRA",
    "ZBH",
    "ZTS",
    "RY.TO",
    "TD.TO",
    "ENB.TO",
    "CNQ.TO",
    "CP.TO",
    "CNR.TO",
    "BMO.TO",
    "BNS.TO",
    "CM.TO",
    "MFC.TO",
    "SU.TO",
    "ABX.TO",
    "SHOP.TO",
    "TRP.TO",
    "BCE.TO",
    "AEM.TO",
    "BAM.TO",
    "WPM.TO",
    "L.TO",
    "T.TO",
    "POW.TO",
    "QSR.TO",
    "ATD.TO",
    "SLF.TO",
    "IFC.TO",
    "FTS.TO",
    "NTR.TO",
    "NA.TO",
    "RCI-B.TO",
    "CVE.TO",
    "CCO.TO",
    "PPL.TO",
    "WSP.TO",
    "WCN.TO",
    "GWO.TO",
    "EMA.TO",
    "CAE.TO",
    "MG.TO",
    "GIB-A.TO",
    "FFH.TO",
    "FM.TO",
    "DOL.TO",
    "MRU.TO",
    "H.TO",
    "FNV.TO",
    "OTEX.TO",
    "BTO.TO",
    "EQB.TO",
    "K.TO",
    "WN.TO",
    "IMO.TO",
    "SAP.TO",
    "AC.TO",
    "AQN.TO",
    "AGI.TO",
    "PKI.TO",
    "TOU.TO",
    "X.TO",
    "SNC.TO",
    "TIH.TO",
    "CSU.TO",
    "TFII.TO",
    "FSV.TO",
    "ATZ.TO",
    "CTC-A.TO",
    "ATA.TO",
    "CLS.TO",
    "WFG.TO",
    "BYD.TO",
    "MX.TO",
    "IFP.TO",
    "LIF.TO",
    "HBM.TO",
    "RUS.TO",
    "NWC.TO",
    "CPX.TO",
    "RBA.TO",
    "AIF.TO",
    "LGT-B.TO",
    "LSPD.TO",
    "ERO.TO",
    "FRU.TO",
    "GEI.TO",
    "LUG.TO",
    "ARM",
    "NET",
    "SNOW",
    "ZS",
    "PINS",
    "RBLX",
    "SNAP",
    "RIVN",
    "MDB",
    "OKTA",
    "LYFT",
    "SOFI"
]
