<?php

/** 
 * Název:            test.php
 * Předmět:          Principy programovacích jazyků a OOP
 * Instituce:        VUT FIT
 * Autor:            Pavel Bobčík
 * Login:            xbobci03
 * vytvořeno:        25. února 2021
 */

// Konstanta, jenž se nastaví v případě chybějícího .rc souboru
define("EXIT_CODE_NOT_FOUND", 0);

// Základní nastavení pro jednotlivé přepínače
$parseFile = "parse.php";
$testFile = getcwd();
$intFile = "interpret.py";
$jexamxmlFile = "/pub/courses/ipp/jexamxml/jexamxml.jar";
$jexamcfgFile = "/pub/courses/ipp/jexamxml/options";
$recursive = false;
$parseOnly = false;
$intOnly = false;

// Pomocné kontrolní logické proměnné
$intScript = false;
$parseScript = false;

// Text pro nápovědu
$help = "+ spuštění              php7.3 test.php [optins] >html
+ --help                zobrazení nápovědy
+ --directory=path      nastavení cesty k testovaným souborům (jinak je nastaven aktuální aresář)
+ --recursive           prohledávání včetně podadresářů
+ --parse-script=file   nastavení cesty ke skriptu parse (jinak se hledá v aktuálním adresáři)
+ --int-script=file     nastavení cesty ke skriptu interpret (jinak se hledá v aktuálním adresáři)
+ --parse-only          zapne testování pouze skriptu parse
+ --int-only            zapne testování pouze skriptu interpret
+ --jexamxml=file       nastavení cesty k JAR JExamXML (jinak se uvažuje cesta na merlinovi)
+ --jexamcfg=file       nastavení cesty ke konfiguraci JExamXML (jinak se uvažuje cesta na merlinovi)\n";

// Proměnné nesoucí informace o průběhu testů
$exitCodeExpec = 0;
$testCounter = 0;
$testCorrectCounter = 0;
$testIncorrectCounter = 0;
$incorrectFilesArray = array();
$correctFilesArray = array();

// Provedení testů
checkArg($argc, $argv);
test();
removeTmpFiles();

exit(0);

/****************
 * Funkce programu
 *****************/


/**
 * Funkce slouží ke kontrole a načtení argumentů, hodnoty uloží do globálních proměnných
 * @param argc počet argumentů
 * @param argv pole argumentů
 */
function checkArg($argc, $argv)
{
    global $parseFile;
    global $testFile;
    global $intFile;
    global $jexamxmlFile;
    global $jexamcfgFile;
    global $recursive;
    global $parseOnly;
    global $intOnly;
    global $intScript;
    global $parseScript;
    global $help;

    if ($argc == 1) {
        // Argument nebyl uveden
        errorCode("Chybející parametr skriptu.", 10);
    } else {
        for ($i = 1; $i < $argc; $i++) {
            $param = explode("=", $argv[$i]);
            switch ($param[0]) {
                    // Byl uveden argument na výpis nápovědy
                case "-h":
                case "--help":
                    if ($argc == 2) {
                        echo $help;
                        exit(0);
                    } else {
                        errorCode("Chybná kombinace parametrů skriptu.", 10);
                    }
                case "--recursive":
                    // Testy bude hledat nejen v zadaném adresáři, ale i rekurzivně ve všech jeho podadresářích
                    $recursive = true;
                    break;
                case "--parse-only":
                    // Bude testován pouze skript pro analýzu zdrojového kódu v IPPcode21
                    $parseOnly = true;
                    break;
                case "--int-only":
                    // Bude testován pouze skript pro interpret XML reprezentace kódu v IPPcode21
                    $intOnly = true;
                    break;
                case "--directory":
                    // Testy bude hledat v zadaném adresáři (chybí-li tento parametr, tak skript prochází aktuální adresář)
                    if ($param[1] != "") {
                        $testFile = $param[1];
                    } else {
                        errorCode("chybné použití parametru --directory=file", 10);
                    }
                    break;
                case "--parse-script":
                    /* 
                    * Soubor se skriptem v PHP 7.4 pro analýzu zdrojového kódu v IPP-code21 
                    * (chybí-li tento parametr, tak implicitní hodnotou je parse.php uložený v aktuálním adresáři)
                    */
                    if ($param[1] != "") {
                        $parseFile = $param[1];
                        $parseScript = true;
                    } else {
                        errorCode("chybné použití parametru --parse-script=file", 10);
                    }
                    break;
                case "--int-script":
                    /* 
                    * Soubor se skriptem v Python 3.8 pro interpret XML reprezentace kódu v IPPcode21 
                    * (chybí-li tento parametr, tak implicitní hodnotou je interpret.py uložený v aktuálním adresáři)
                    */
                    if ($param[1] != "") {
                        $intFile = $param[1];
                        $intScript = true;
                    } else {
                        errorCode("chybné použití parametru --int-script=file", 10);
                    }
                    break;
                case "--jexamxml":
                    /* 
                    * soubor s JAR balíčkem s nástrojem A7Soft JExamXML. Je-li parametr vynechán uvažuje se implicitní umístění 
                    * /pub/courses/ipp/jexamxml/jexamxml.jar na ser- veru Merlin, kde bude test.php hodnocen.
                    */
                    if ($param[1] != "") {
                        if (!$jexamxmlFile = realpath($param[1])) {
                            errorCode("Chyba při přístupu k souboru jexamxml.jar.\n", 41);
                        }
                    } else {
                        errorCode("Chybné použití parametru --jexamxml=file", 10);
                    }
                    break;
                case "--jexamcfg":
                    /* 
                    * soubor s konfigurací nástroje A7SoftJExamXML. Je-li parametr vynechán uvažuje se implicitní umístění 
                    * /pub/courses/ipp/jexamxml/options na serveru Merlin, kde bude test.php hodnocen.
                    */
                    if ($param[1] != "") {
                        if (!$jexamcfgFile = realpath($param[1])) {
                            errorCode("Chyba při přístupu k souboru options.\n", 41);
                        }
                    } else {
                        errorCode("Chybné použití parametru --jexamcfg=file", 10);
                    }
                    break;
                default:
                    errorCode("Chybný argmuent.", 10);
                    break;
            }
        }
    }

    if (($parseOnly && ($intOnly || $intScript)) || ($intOnly && ($parseOnly || $parseScript))) {
        errorCode("Chybná kombinace parametrů skriptu.", 10);
    }
}

/** 
 * Funkce pro ukončení skriptu s chybovým hlášením a kódem
 * @param errorMsg chybové hlášení
 * @param errorNum chybový kód
 */
function errorCode($errorMsg, $errorNum)
{
    fwrite(STDERR, $errorMsg . "\n");
    removeTmpFiles();
    exit($errorNum);
}

/**
 * Funkce sloužící k odstranění dočasných souborů
 */
function removeTmpFiles()
{
    if (is_file("_@parseOut.tmp")) {
        unlink("_@parseOut.tmp");
    }
    if (is_file("_@interpretOut.tmp")) {
        unlink("_@interpretOut.tmp");
    }
    if (is_file("_@errorMessage.tmp")) {
        unlink("_@errorMessage.tmp");
    }
    if (is_file("delta.xml")) {
        unlink("delta.xml");
    }
}

/**
 * Funkce sloužící k vykonání testů na základě nastavení přepínačů
 */
function test()
{
    global $recursive;
    global $parseFile;
    global $intFile;
    global $testFile;
    global $parseOnly;
    global $intOnly;
    global $testCounter;

    $files = (object) null;

    // Získání pole souborů k otestování
    if ($recursive == false) {
        try {
            $files = new DirectoryIterator($testFile);
        } catch (Exception $ex) {
            errorCode("Chyba při procházení souborů. Viz výjmka:\n" . $ex, 41);
        }
    } else {
        try {
            $recFiles = new RecursiveDirectoryIterator($testFile);
            $files = new RecursiveIteratorIterator($recFiles);
        } catch (Exception $ex) {
            errorCode("Chyba při rekurzivním procházení souborů. Viz výjmka:\n" . $ex, 41);
        }
    }

    // Procházení jednotlivých souborů z pole
    foreach ($files as $file) {
        if ($file->getExtension() == "src") {
            if ($recursive == false) {
                $file = $file->getPathname();
            }
            $testCounter++;
            if ($parseOnly) {
                // Procházení v případě, že se jedná pouze o --parse-only
                if (!is_file($parseFile)) {
                    errorCode("Uvedený soubor se skriptem parse.php neexistuje.", 41);
                }
                exec("php7.3 " . $parseFile . " <" . $file . " >_@parseOut.tmp 2>>_@errorMessage.tmp", $tmp, $exitCodeRec);

                createMissingFiles($file);
                $exitCodeRec = trim($exitCodeRec);
                $endWithError = parse($file, $exitCodeRec);
                if ($endWithError) {
                    continue;
                }
            } else if (!$parseOnly && !$intOnly) {
                // Procházení v případě, že se jedná o oba skripty
                if (!is_file($parseFile)) {
                    errorCode("Uvedený soubor se skriptem parse.php neexistuje.", 41);
                }
                exec("php7.3 " . $parseFile . " <" . $file . " >_@parseOut.tmp 2>>_@errorMessage.tmp", $tmp, $exitCodeRec);

                createMissingFiles($file);
                $exitCodeRec = trim($exitCodeRec);

                if ($exitCodeRec != 0) {
                    $endWithError = parse($file, $exitCodeRec);
                    if ($endWithError) {
                        continue;
                    }
                } else {
                    if (!is_file($intFile)) {
                        errorCode("Uvedený soubor se skriptem interpret.py neexistuje.", 41);
                    }

                    $endWithError = interpret($file, "_@parseOut.tmp");

                    if ($endWithError) {
                        continue;
                    }
                }
            } else {
                // Procházení v případě, že se jedná pouze o --int-only
                if (!is_file($intFile)) {
                    errorCode("Uvedený soubor se skriptem interpret.py neexistuje.", 41);
                }

                createMissingFiles($file);
                $endWithError = interpret($file, $file);

                if ($endWithError) {
                    continue;
                }
            }
        }
    }
    makeHtml();
}

/**
 * Funkce pro vykonání kontroly skriptu parse.php
 * @param file testovaný soubor
 * @param exitCodeRec obdržený exit code z vykonaného skriptu parse.php
 * @return Boolean pravidvostní hodnotu, zda-li skript skončil s chybovým kódem
 */
function parse($file, $exitCodeRec)
{
    global $jexamcfgFile;
    global $jexamxmlFile;
    global $exitCodeExpec;
    global $testCorrectCounter;
    global $testIncorrectCounter;
    global $parseScript;

    global $incorrectFilesArray;
    global $correctFilesArray;

    $file = preg_replace("/(src)$/", "rc", $file);
    $exitCodeExpec = rcFileOperation($file);

    // Zkontroluje se shoda s očekávaným chybovým kódem
    if (compareExitCodes($exitCodeExpec, $exitCodeRec) == false) {
        $testIncorrectCounter++;
        $tmpError = new errorArray($file, "Exit kód", "Očekávaný exit kód: " . $exitCodeExpec, "Obdržený exit kód: " . $exitCodeRec);
        array_push($incorrectFilesArray, $tmpError);
        fwrite(STDERR, "Chyba exit code v: " . $file . "\n");
        return true;
    }

    // Pokud není chybový kód 0 (správný výstup), tak se další kontroly výstupu neprovádí
    if ($exitCodeRec != 0) {
        $testCorrectCounter++;
        $file = preg_replace("/(rc)$/", "src", $file);
        array_push($correctFilesArray, $file);
        return true;
    }

    $file = preg_replace("/(rc)$/", "out", $file);

    // Kontrola výstupního XML
    if ($parseScript) {
        exec("java -jar " . $jexamxmlFile . " _@parseOut.tmp " . $file . " delta.xml " . $jexamcfgFile, $output, $xmlExitCode);
        if ($xmlExitCode == 0) {
            $file = preg_replace("/(out)$/", "src", $file);
            array_push($correctFilesArray, $file);
            $testCorrectCounter++;
        } else {
            $testIncorrectCounter++;
            $tmpError = new errorArray($file, "XML porovnání", "", "");
            array_push($incorrectFilesArray, $tmpError);
            fwrite(STDERR, "Chyba xml v: " . $file . "\n");
        }
    }
    return false;
}

/**
 * Funkce pro vykonání kontroly skriptu parse.php
 * @param file testovaný soubor
 * @param srcFile soubor obsahující vstup (může se lišit od vstupního, pokud se vykonávají oba testy)
 * @return Boolean pravidvostní hodnotu, zda-li skript skončil s chybovým kódem
 */
function interpret($file, $srcFile)
{
    global $intFile;
    global $exitCodeExpec;
    global $testCorrectCounter;
    global $testIncorrectCounter;

    global $incorrectFilesArray;
    global $correctFilesArray;

    $fileIn = preg_replace("/(src)$/", "in", $file);
    exec("python3.8 " . $intFile . " --source=" . $srcFile . " --input=" . $fileIn . " >_@interpretOut.tmp 2>>_@errorMessage.tmp", $tmp, $exitCodeRec);

    $file = preg_replace("/(src)$/", "rc", $file);
    $exitCodeExpec = rcFileOperation($file);
    $exitCodeRec = trim($exitCodeRec);

    if (compareExitCodes($exitCodeExpec, $exitCodeRec) == false) {
        $testIncorrectCounter++;
        $tmpError = new errorArray($file, "Exit kód", "Očekávaný exit kód: " . $exitCodeExpec, "Obdržený exit kód: " . $exitCodeRec);
        array_push($incorrectFilesArray, $tmpError);
        fwrite(STDERR, "Chyba exit code v: " . $file . "\n");
        return true;
    }

    if ($exitCodeRec != 0) {
        $testCorrectCounter++;
        $file = preg_replace("/(rc)$/", "src", $file);
        array_push($correctFilesArray, $file);
        return true;
    }

    $file = preg_replace("/(rc)$/", "out", $file);

    exec("diff _@interpretOut.tmp " . $file, $tmp, $diffExitCode);
    if ($diffExitCode == 0) {
        $file = preg_replace("/(out)$/", "src", $file);
        array_push($correctFilesArray, $file);
        $testCorrectCounter++;
    } else {
        $out = "";
        for ($i = 0; $i < count($tmp); $i++) {
            $out = $out . $tmp[$i];
        }
        $testIncorrectCounter++;
        $tmpError = new errorArray($file, "Odlišný výstup interpret.py", "", $out);
        array_push($incorrectFilesArray, $tmpError);
        fwrite(STDERR, "Odlišný out v: " . $file . "\n");
    }
    return false;
}

/**
 * Funkce na získání očekávaného chybového kódu
 * @param file testovaný soubor
 * @return exitCode chybový kód
 */
function rcFileOperation($file)
{
    $exitCode = EXIT_CODE_NOT_FOUND;

    $fileStream = fopen($file, "r");
    if (!$fileStream) {
        errorCode("Chyba při otevření souboru\n", 41);
    } else {
        $exitCode = fgets($fileStream);
    }

    if (!fclose($fileStream)) {
        errorCode("Chyba při uzavření souboru\n", 99);
    }

    if (empty($exitCode)) {
        $exitCode = EXIT_CODE_NOT_FOUND;
    }
    return $exitCode;
}

/**
 * Funkce na porovnání chybového kódu
 * @param exitCodeExpec očekávaný chybový kód
 * @param exitCodeRec obdržený chybový kód
 * @return Boolean pravdivostní hodnotu, zda-li se rovnají či nikoliv
 */
function compareExitCodes($exitCodeExpec, $exitCodeRec)
{
    $exitCodeExpec = trim($exitCodeExpec);
    if (preg_match("/[^0-9]+/", $exitCodeExpec) || $exitCodeExpec == "") {
        errorCode("Neplatný exit code.\n", 99);
    }

    if ($exitCodeExpec != $exitCodeRec) {
        return false;
    }
    return true;
}

/**
 * Funkce vytvoří chybějící testované soubory (.rc, .in, .out)
 * @param file testovaný soubor
 */
function createMissingFiles($file)
{
    $file = preg_replace("/(src)$/", "in", $file);
    if (!file_exists($file)) {
        $fileStream = fopen($file, "w+");
        if (!$fileStream) {
            errorCode("Chyba při vytváření souboru\n", 41);
        }
    }

    $file = preg_replace("/(in)$/", "out", $file);
    if (!file_exists($file)) {
        $fileStream = fopen($file, "w+");
        if (!$fileStream) {
            errorCode("Chyba při vytváření souboru\n", 41);
        }
    }

    $file = preg_replace("/(out)$/", "rc", $file);
    $fileStream = NULL;
    if (!file_exists($file)) {
        $fileStream = fopen($file, "w+");
        if (!$fileStream) {
            errorCode("Chyba při vytváření souboru\n", 41);
        } else {
            if (!fwrite($fileStream, EXIT_CODE_NOT_FOUND)) {
                errorCode("Chyba při zapisování do souboru\n", 41);
            } else {
                if (!fclose($fileStream)) {
                    errorCode("Chyba při uzavření souboru\n", 99);
                }
            }
        }
    }
}

/**
 * Klíč pro usort, třídění dle názvu souboru
 * @param a první prvek k porovnání
 * @param b druhý prvek k porovnání
 * @return int hodnotu porovnání 
 */
function compare($a, $b)
{
    return strcmp($a->file, $b->file);
}

/**
 * Funkce na vytvoření HTML výstupu
 */
function makeHtml()
{
    global $testFile;
    global $recursive;
    global $intOnly;
    global $parseOnly;
    global $incorrectFilesArray;
    global $correctFilesArray;
    global $testCounter;
    global $testCorrectCounter;
    global $testIncorrectCounter;

    // Seřazení pole
    if (!empty($incorrectFilesArray)) {
        usort($incorrectFilesArray, "compare");
    }
    if (!empty($correctFilesArray)) {
        asort($correctFilesArray);
    }

    // Inicializování HTML, vytvoření hlavičky a těla, přidání popisku okna
    $dom = new DOMDocument("1.0", "utf-8");
    $htmlMarker = $dom->createElement("html");
    $headMarker = $dom->createElement("head");
    $titleText = "IPP21 - souhrn testů";
    $title = $dom->createElement("title", $titleText);
    $bodyMarker = $dom->createElement("body");
    $br = $dom->createElement("br");
    // --------------------------

    // Nastavení stylu tabulek
    $tableBorderTableBorder = "table, th, td {border: 1px solid black; border-collapse: collapse;}";
    $styleMarkerTableBorder = $dom->createElement("style", $tableBorderTableBorder);
    $domAttributeTableBorder = $dom->createAttribute("type");
    $domAttributeTableBorder->value = "text/css";
    $styleMarkerTableBorder->appendChild($domAttributeTableBorder);

    $tableBorderTableSpace = "td {padding: 2 15px 2 5px;}";
    $styleMarkerTableSpace = $dom->createElement("style", $tableBorderTableSpace);
    $domAttributeTableSpace = $dom->createAttribute("type");
    $domAttributeTableSpace->value = "text/css";
    $styleMarkerTableSpace->appendChild($domAttributeTableSpace);
    // --------------------------

    // Tabulka s vyhodnocením testů
    $headlineTable = $dom->createElement("h2", "Vyhodnocení testů");

    $table = $dom->createElement("table");

    $tr = $dom->createElement("tr");
    $table->appendChild($tr);

    $td = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Úspěšných:");
    $linkMarkerSucc = $dom->createElement("a");
    $domAttributeLinkSucc = $dom->createAttribute("href");
    $domAttributeLinkSucc->value = "#uspech";
    $linkMarkerSucc->appendChild($domAttributeLinkSucc);
    $linkMarkerSucc->appendChild($boldMarker);
    $td->appendChild($linkMarkerSucc);
    $tr->appendChild($td);

    $td = $dom->createElement("td", $testCorrectCounter . "/" . $testCounter);
    $tr->appendChild($td);

    $tr = $dom->createElement("tr");
    $table->appendChild($tr);

    $td = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Neúspěšných:");
    $linkMarkerFail = $dom->createElement("a");
    $domAttributeLinkFail = $dom->createAttribute("href");
    $domAttributeLinkFail->value = "#neuspech";
    $linkMarkerFail->appendChild($domAttributeLinkFail);
    $linkMarkerFail->appendChild($boldMarker);
    $td->appendChild($linkMarkerFail);
    $tr->appendChild($td);

    $td = $dom->createElement("td", $testIncorrectCounter . "/" . $testCounter);
    $tr->appendChild($td);

    $tr = $dom->createElement("tr");
    $table->appendChild($tr);

    $td = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Úspěšnost:");
    $td->appendChild($boldMarker);
    $tr->appendChild($td);

    if ($testCounter > 0) {
        $td = $dom->createElement("td", round(($testCorrectCounter / $testCounter) * 100.0, 2) . "%");
    } else {
        $td = $dom->createElement("td", "---");
    }
    $tr->appendChild($td);

    $dom->appendChild($table);
    // --------------------------

    // Tabulka s nastavením testů
    $headlineTableSetting = $dom->createElement("h2", "Nastavení testů");

    $tableSetting = $dom->createElement("table");

    $trSetting = $dom->createElement("tr");
    $tableSetting->appendChild($trSetting);

    $tdSetting = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Directory:");
    $tdSetting->appendChild($boldMarker);
    $tableSetting->appendChild($tdSetting);

    $tdSetting = $dom->createElement("td", $testFile);
    $tableSetting->appendChild($tdSetting);

    $trSetting = $dom->createElement("tr");
    $tableSetting->appendChild($trSetting);

    $tdSetting = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Recursive:");
    $tdSetting->appendChild($boldMarker);
    $tableSetting->appendChild($tdSetting);

    if ($recursive) {
        $tdSetting = $dom->createElement("td", "True");
    } else {
        $tdSetting = $dom->createElement("td", "False");
    }
    $tableSetting->appendChild($tdSetting);

    $trSetting = $dom->createElement("tr");
    $tableSetting->appendChild($trSetting);

    $tdSetting = $dom->createElement("td");
    $boldMarker = $dom->createElement("b", "Script:");
    $tdSetting->appendChild($boldMarker);
    $tableSetting->appendChild($tdSetting);

    if ($parseOnly) {
        $tdSetting = $dom->createElement("td", "parse.php");
    } else if ($intOnly) {
        $tdSetting = $dom->createElement("td", "interpret.py");
    } else {
        $tdSetting = $dom->createElement("td", "both");
    }
    $tableSetting->appendChild($tdSetting);
    // --------------------------

    // Tabulka s neúspěšnými testy
    $headlineFail = $dom->createElement("h2", "Neúspěšné testy");
    $domAttributeHeadlineFail = $dom->createAttribute("id");
    $domAttributeHeadlineFail->value = "neuspech";
    $headlineFail->appendChild($domAttributeHeadlineFail);

    if (!empty($incorrectFilesArray)) {
        $tableFail = $dom->createElement("table");

        $trFail = $dom->createElement("tr");
        $tableFail->appendChild($trFail);

        $tdFail = $dom->createElement("td");
        $boldMarker = $dom->createElement("b", "Typ chyby:");
        $tdFail->appendChild($boldMarker);
        $tableFail->appendChild($tdFail);

        $tdFail = $dom->createElement("td");
        $boldMarker = $dom->createElement("b", "Testovaný soubor:");
        $tdFail->appendChild($boldMarker);
        $tableFail->appendChild($tdFail);

        $tdFail = $dom->createElement("td");
        $boldMarker = $dom->createElement("b", "Očekávaný výstup:");
        $tdFail->appendChild($boldMarker);
        $tableFail->appendChild($tdFail);

        $tdFail = $dom->createElement("td");
        $boldMarker = $dom->createElement("b", "Obdržený výstup:");
        $tdFail->appendChild($boldMarker);
        $tableFail->appendChild($tdFail);

        foreach ($incorrectFilesArray as $arrayOut) {
            $trFail = $dom->createElement("tr");
            $tableFail->appendChild($trFail);

            $tdFail = $dom->createElement("td", $arrayOut->typeOfError);
            $tableFail->appendChild($tdFail);

            $tdFail = $dom->createElement("td", $arrayOut->file);
            $tableFail->appendChild($tdFail);

            $tdFail = $dom->createElement("td", htmlspecialchars($arrayOut->detailsFirst));
            $tableFail->appendChild($tdFail);

            $tdFail = $dom->createElement("td", htmlspecialchars($arrayOut->detailsSecond));
            $tableFail->appendChild($tdFail);
        }
    } else {
        $emptyFail = $dom->createElement("p", "Všechny testy proběhly úspěšně.");
    }
    // --------------------------

    // Tabulka s úspěšnými testy
    $headlineSucc = $dom->createElement("h2", "Úspěšné testy");
    $domAttributeHeadlineSucc = $dom->createAttribute("id");
    $domAttributeHeadlineSucc->value = "uspech";
    $headlineSucc->appendChild($domAttributeHeadlineSucc);

    if (!empty($correctFilesArray)) {
        $tableSucc = $dom->createElement("table");

        $trSucc = $dom->createElement("tr");
        $tableSucc->appendChild($trSucc);

        $tdSucc = $dom->createElement("td");
        $boldMarker = $dom->createElement("b", "Testovaný soubor:");
        $tdSucc->appendChild($boldMarker);
        $tableSucc->appendChild($tdSucc);

        foreach ($correctFilesArray as $arrayOut) {
            $trSucc = $dom->createElement("tr");
            $tableSucc->appendChild($trSucc);

            $tdSucc = $dom->createElement("td", $arrayOut);
            $tableSucc->appendChild($tdSucc);
        }
    } else {
        $emptySucc = $dom->createElement("p", "Všechny testy selhaly.");
    }
    // --------------------------

    // Vypsání vytvořených elementů do HTML souboru
    $headMarker->appendChild($title);
    $headMarker->appendChild($styleMarkerTableBorder);
    $headMarker->appendChild($styleMarkerTableSpace);

    $bodyMarker->appendChild($headlineTable);
    $bodyMarker->appendChild($table);
    $bodyMarker->appendChild($br);

    $bodyMarker->appendChild($headlineTableSetting);
    $bodyMarker->appendChild($tableSetting);
    $bodyMarker->appendChild($br);

    $bodyMarker->appendChild($headlineFail);
    if (!empty($incorrectFilesArray)) {
        $bodyMarker->appendChild($tableFail);
    } else {
        $bodyMarker->appendChild($emptyFail);
    }
    $bodyMarker->appendChild($br);

    $bodyMarker->appendChild($headlineSucc);
    if (!empty($correctFilesArray)) {
        $bodyMarker->appendChild($tableSucc);
    } else {
        $bodyMarker->appendChild($emptySucc);
    }
    $bodyMarker->appendChild($br);

    $htmlMarker->appendChild($headMarker);
    $htmlMarker->appendChild($bodyMarker);
    $dom->appendChild($htmlMarker);
    $dom->normalizeDocument();

    // Výpis HTML na standartní výstup
    echo $dom->saveHTML();
}

/**
 * Pomocná třída prvků pro pole chybných testů
 */
class errorArray
{
    var $typeOfError;
    var $file;
    var $details;

    function __construct($par1, $par2, $par3, $par4)
    {
        $this->file = $par1;
        $this->typeOfError = $par2;
        $this->detailsFirst = $par3;
        $this->detailsSecond = $par4;
    }
}
