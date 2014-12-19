<?php
	/*



/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Time=2014-12-16T17:14:53Z
/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/DistanceMeters=97.86
/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/HeartRateBpm/Value=104
/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Cadence=71
/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Extensions/ns3:TPX/ns3:Watts=166
/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Extensions/ns3:TPX/ns3:Speed=5.66166666666667


 case 21 : // TACX FLOW SETTING 2
{
double V = rtData.getSpeed();
double slope = 9.51;
double intercept = -66.69;
rtData.setWatts((slope * V) + intercept);
}
break;

*/

	$l = file("xml.txt");
	foreach($l as $line){
		if(preg_match('#/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint$#', $line)){

			$kmspeed = $speed * 3.6;
			$mph = $speed * 3.6 * 0.621371;
			$slope = 7.75;
			$intercept = -47.27;
			$fejkwatt = ($slope * $kmspeed) + $intercept;

			$slope = 9.51;
			$intercept = -66.69;
			$twofejkwatt = ($slope * $kmspeed) + $intercept;

			$slope = 15.05;
			$intercept = -45.86666667;
			$trwatt = ($slope * $mph) + $intercept;



			$kfejkwatt =  6.88964+3.92273 *$kmspeed +0.102844 * $kmspeed*$kmspeed;
			$kfejkwatt = -85.5128+10.6806* $kmspeed-0.00427179* $kmspeed * $kmspeed;
			$ktwofejkwatt = -85.5128+10.6806* $kmspeed-0.00427179* $kmspeed * $kmspeed;
			$k3fekwatt =  -341.991+37.1314 *$kmspeed-0.878102 *$kmspeed*$kmspeed+0.00922628 *$kmspeed*$kmspeed*$kmspeed;

			echo $time, " ", $w, " ", $fejkwatt , " ", $kfejkwatt, " ", $twofejkwatt, " ", $ktwofejkwatt, " ", $k3fekwatt, " ", $trwatt, " ",  $speed, "\n";
			$time = 0;
			$w = 0; 
			$speed = 0;
		}

		if(preg_match('#/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Time=(.*)#', $line, $s)){
			$time = $s[1];
		}

		if(preg_match('#/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Extensions/ns3:TPX/ns3:Speed=(.*)#', $line, $s)){
			$speed = $s[1];
		}

		if(preg_match('#/TrainingCenterDatabase/Activities/Activity/Lap/Track/Trackpoint/Extensions/ns3:TPX/ns3:Watts=(.*)#', $line, $s)){
			$w = $s[1];
		}


	}

?>
