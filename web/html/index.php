<?php
set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

include_once("aur.inc.php");
include_once("pkgfuncs.inc.php");

$path = $_SERVER['PATH_INFO'];
$tokens = explode('/', $path);

if (isset($tokens[1]) && '/' . $tokens[1] == get_pkg_route()) {
	if (isset($tokens[2])) {
		/* TODO: Create a proper data structure to pass variables from
		 * the routing framework to the individual pages instead of
		 * initializing arbitrary variables here. */
		$pkgname = $tokens[2];
		$pkgid = pkgid_from_name($pkgname);

		if (isset($tokens[3])) {
			if ($tokens[3] == 'voters') {
				$_GET['ID'] = pkgid_from_name($tokens[2]);
				include('voters.php');
				return;
			}

			/* TODO: Remove support for legacy URIs and move these
			 * actions to separate modules. */
			switch ($tokens[3]) {
			case "vote":
				$_POST['do_Vote'] = __('Vote');
				break;
			case "unvote":
				$_POST['do_UnVote'] = __('UnVote');
				break;
			case "notify":
				$_POST['do_Notify'] = __('Notify');
				break;
			case "unnotify":
				$_POST['do_UnNotify'] = __('UnNotify');
				break;
			case "flag":
				$_POST['do_Flag'] = __('Flag');
				break;
			case "unflag":
				$_POST['do_UnFlag'] = __('UnFlag');
				break;
			case "delete":
				include('pkgdel.php');
				return;
			}

			if (isset($_COOKIE['AURSID'])) {
				$_POST['token'] = $_COOKIE['AURSID'];
			}

			$_POST['IDs'] = array(pkgid_from_name($tokens[2]) => '1');
		}
	}

	include get_route('/' . $tokens[1]);
} elseif (isset($tokens[1]) && '/' . $tokens[1] == get_user_route()) {
	if (isset($tokens[2])) {
		$_REQUEST['U'] = $tokens[2];

		if (isset($tokens[3])) {
			if ($tokens[3] == 'edit') {
				$_REQUEST['Action'] = "DisplayAccount";
			} elseif ($tokens[3] == 'update') {
				$_REQUEST['Action'] = "UpdateAccount";
			} else {
				$_REQUEST['Action'] = "AccountInfo";
			}
		} else {
			$_REQUEST['Action'] = "AccountInfo";
		}
	}
	include get_route('/' . $tokens[1]);
} elseif (get_route($path) !== NULL) {
	include get_route($path);
} else {
	switch ($path) {
	case "/css/archweb.css":
	case "/css/aur.css":
	case "/css/archnavbar/archnavbar.css":
		header("Content-Type: text/css");
		include "./$path";
		break;
	case "/css/archnavbar/archlogo.gif":
	case "/images/new.png":
		header("Content-Type: image/png");
		include "./$path";
		break;
	case "/css/archnavbar/archlogo.png":
	case "/images/AUR-logo-80.png":
	case "/images/AUR-logo.png":
	case "/images/favicon.ico":
	case "/images/feed-icon-14x14.png":
	case "/images/titlelogo.png":
	case "/images/x.png":
		header("Content-Type: image/png");
		include "./$path";
		break;
	}
}
