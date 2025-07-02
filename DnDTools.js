//Clock for the sync loop
let clock;

//Timer variables
d = new Date();
i_time = d.getTime();
clock = 0

//websocket message up here in global
let WSmessage,fullHist,sendStringPrev;
WSmessage = "";
fullHist = ""; //History of all results
sendStringPrev = ""; //check for double-sends

//Make the actual websocket
sock = new WebSocket('ws://127.0.0.1:8080');

//websocket callbacks
sock.onopen = function(event){setElement("state","opened");};
sock.onmessage = function(event){onReply(event);};
sock.onclose = function(event){setElement("state","closed");};

//Start up the main loop at 10ms intervals
setInterval(tickTock,10);

//List of splash and poster images- ambience!
let splashImages,r;
splashImages = ['imgs/amateur mage 2.jpeg', 'imgs/amateur mage 1.jpeg', 'imgs/dragon 2.jpeg', 'imgs/new gata.jpeg', 'imgs/voss flavor 2.jpeg', 'imgs/scuriat clock.jpeg', 'imgs/dwarf 3.jpeg', 'imgs/old elf 2.jpeg', 'imgs/half orc 6.jpeg', 'imgs/handsome rat.jpeg', 'imgs/ursa flavor k 1.jpeg', 'imgs/scuriat cock 2.jpeg', 'imgs/scuriat flavor l 2.jpeg', 'imgs/cooking lupa.jpeg'];
posterImages = ['posters/warking 18.jpeg', 'posters/shrine 1.jpeg', 'posters/scene 7.jpeg', 'posters/travelers 10.jpeg', 'posters/edge of yllea A 1.jpeg', 'posters/strype border 2.jpeg', 'posters/vista 9.jpeg', 'posters/village 6.jpeg', 'posters/moressley 7.jpeg', 'posters/warking 11.jpeg', 'posters/Millstone 2.jpeg', 'posters/rune 9.jpeg', 'posters/village 4.jpeg', 'posters/market 3.jpeg', 'posters/pastoral village 1.jpeg', 'posters/ruins 3.jpeg', 'posters/cliff beach 5.jpeg', 'posters/vista k 27.jpeg', 'posters/charred 1.jpeg', 'posters/scene 3.jpeg', 'posters/outpost 1.jpeg', 'posters/vista k 25.jpeg', 'posters/vista k 12.jpeg', 'posters/scene 43.jpeg', 'posters/cliff beach 2.jpeg', 'posters/forboding range 1.jpeg', 'posters/tenders 5.jpeg', 'posters/storm 5.jpeg', 'posters/road 1.jpeg', 'posters/warking 2.jpeg', 'posters/vista k 17.jpeg', 'posters/passage 2.jpeg', 'posters/vista k 16.jpeg', 'posters/desert travel 1.jpeg', 'posters/Maharin 8.jpeg', 'posters/warking 4.jpeg', 'posters/elementalists 3.jpeg', 'posters/vista 1.jpeg', 'posters/storm A 1.jpeg','posters/fireplace1.gif','posters/fireplace2.gif','posters/fireplace3.gif','posters/fireplace4.gif']

//Load a random splash image every time
r = Math.random();
r = Math.floor(r*splashImages.length)
document.getElementById('splashImage').src = splashImages[r];

//Load a random poster image every time
r = Math.random();
r = Math.floor(r*posterImages.length)
document.getElementById('posterImage').src = posterImages[r];

//Variables for the combat manager
//	*Background, die rolls, and magic items are over in Python, combat manager is mostly here
let nCombatants,combatants,cProto,updateCombs,toInitCombs,didRoll,currentTurn,turnAdvanced;
nCombatants = 0; //Number of them there are
combatants = []; //List of [divElement,initiative] for sorting and showing
updateCombs = false; //Flag to update- set when there's a chanfe
toInitCombs = []; //Data to send along updates for combatants
didRoll = false; //Flag for if a roll was called (to update amount boxes)
currentTurn = 0; //Index of turn to cycle combatant cards
turnAdvanced = false; //Flag for if the turn was cycled

//For empower dies input
let empDiesNumbers;
empDiesNumbers = [];

//Prototype for a combatant card, using Æ as the placeholder for the index number
// We address card properties with segment keys like 'camt_Æ': (c)ard (am)oun(t) _ Æ(index)
cProto = '<b id="cname_Æ" style="margin-left:5px;">Combatant Name</b> <span style="margin-right:5px;float:right">Init <span id="cinit_Æ">2</span></span><br>\n\
<button id="cd_Æ" onclick="cDam(event);" style="height:20px;margin-left:5px;">Dam.</button>\n\
<button id="ch_Æ" onclick="cHeal(event);" style="height:20px;">Heal</button>\n\
<button id="cr_Æ" onclick="cRem(event);" style="height:20px;">Rem.</button>\n\
<input type="number" id="camt_Æ" min="0" style="width:4em;">\n\
<button id="cc_Æ" onclick="cCond(event);" style="height:20px;margin-left:5px;">Cond.</button>\n\
<span id="cndCtr1_Æ" onclick="remCond(event);" style="width:20px;color:DarkRed;display:inline-block;"></span>\n\
<span id="cndCtr2_Æ" onclick="remCond(event);" style="width:20px;color:DarkOrange;display:inline-block;"></span>\n\
<span id="cndCtr3_Æ" onclick="remCond(event);" style="width:20px;color:GoldenRod;display:inline-block;"></span>\n\
<span id="cndCtr4_Æ" onclick="remCond(event);" style="width:20px;color:DarkGreen;display:inline-block;"></span>\n\
<span id="cndCtr5_Æ" onclick="remCond(event);" style="width:20px;color:DarkBlue;display:inline-block;"></span>\n\
<span id="cndCtr6_Æ" onclick="remCond(event);" style="width:20px;color:DarkViolet;display:inline-block;"></span><br/>\n\
<table style="table-layout:fixed;width:100%;margin-top:-10px;margin-bottom:-10px;">\n\
	<tr>\n\
	<td style="vertical-align:top;">\n\
		<pre style="width:100%;border:1px solid red;">HP <span id="cHP_Æ">20</span>\n\
AC <span id="cAC_Æ">13</span></pre>\n\
	</td>\n\
	<td style="vertical-align:top;">\n\
		<pre style="width:100%;border:1px solid red;"><span id="ca1_Æ">Atk1 2d4+2</span>\n\
<span id="ca2_Æ">Atk2 1d6+3</span>\n\
<span id="ca3_Æ">Atk3 1d4+3</span></pre>\n\
	</td>\n\
	</tr>\n\
</table>';

//Header for the right-side results column- put at the top regardless of history
baseResultHTML = "<b><u>Results:</u></b> <span style='float:right;'><button onclick='saveHist();' style='color:green;'>Save History</button> <button onclick='clearHist();' style='color:red;'>Clear History</button></span><hr>"

//Main loop
function tickTock(){
	//Update time
	d = new Date();
	clock = d.getTime()-i_time;
	document.getElementById('clock').innerHTML="Clocktime: "+(clock/1000.0)+"s";

	//If there's a combatant update
	if (updateCombs){

		//Grab the manager div and clear it
		cbtMgr = document.getElementById("cbtMgr");
		cbtMgr.innerHTML = '';

		//Note that you are now, currently, updating the div
		updateCombs = false;

		//Cycle through the candidates to put them in order with the current active card at the top
		for (let i=currentTurn;i<combatants.length;i++){cbtMgr.appendChild(combatants[i][0]);}
		for (let i=0;i<currentTurn;i++){cbtMgr.appendChild(combatants[i][0]);}

		//When you updated because of a turn change
		if (turnAdvanced){
			cmbLead = combatants[currentTurn]; //Grab the current leading card
			cid_N = cmbLead[0].id; //Get its id and number
			N = getCIndex(cid_N)

			//Loop over all condition counters (there's 6 because more looked bad)
			for(let j=1;j<7;j++){
				cndAmt = document.getElementById('cndCtr'+j+'_'+N).innerHTML; //Grab the counter value
				if (cndAmt != ''){ //If it's not empty
					am = parseInt(cndAmt); //Subtract 1 turn and update
					am = am - 1;
					document.getElementById('cndCtr'+j+'_'+N).innerHTML = am;
				}
				//Clear it to '' if the condition is over
				if (am == '0'){document.getElementById('cndCtr'+j+'_'+N).innerHTML = '';}
			}
			turnAdvanced = false; //clear turn advance flag
		}

		//Looping over any initialization updates posted
		for (let j=0;j<toInitCombs.length;j++){

			toInitComb = toInitCombs[j]; //Grab the jth update

			//Update the prototype card's name, hp, ac, and initiative
			document.getElementById('cname_'+toInitComb[0]).innerHTML = toInitComb[1];
			document.getElementById('cHP_'+toInitComb[0]).innerHTML = toInitComb[2];
			document.getElementById('cAC_'+toInitComb[0]).innerHTML = toInitComb[3];
			document.getElementById('cinit_'+toInitComb[0]).innerHTML = toInitComb[4];

			//Update the attacks
			for (let i=0;i<3;i++){
				let l = i+1;
				if (i<toInitComb[5].length){//for up to the three atks in there, get the internal coded span and update it
					document.getElementById('ca'+l+'_'+toInitComb[0]).innerHTML = "Atk"+l+" "+"<span id='cai" + l + "_" + toInitComb[0]+"' style='color:blue;' onclick='loadRoll(event);'>"+toInitComb[5][i]+"</span>";} //Style is to set clickable atks to blue and add the function to roll them when clicked
				else{document.getElementById('ca'+l+'_'+toInitComb[0]).innerHTML = "";} //Otherwise the atk is empty
			}
		}
		toInitCombs = []; //Clear the updates for later
	}
}

//Function to run an empower dies trial with the current list of trial dies
function trial(){

	if (empDiesNumbers.length > 0){
		msg = ''
		for (let i=0;i<empDiesNumbers.length;i++){
			msg = msg + empDiesNumbers[i][0] + "," + empDiesNumbers[i][1] + "," + empDiesNumbers[i][2] + ";";
		}	
		sendString("trial§"+msg);
	}
	else{
		alert("No dies entered!");
	}


}

//Remove an empowerment trial die by clicking on it
function remEmpDie(){
	let cid_N = event.target.id; //Grab the caller's target id
	N = parseInt(getCIndex(cid_N)); //Get the card index from that id

	//New die list after removal and remade div string
	let n_empDiesNumbers = [];
	let empDies = '';

	let j=0; //j will be the index in the new list
	for (let i=0;i<empDiesNumbers.length;i++){//looping over current entried
		if (i!=N){ //If it's not the one to remove
			n_empDiesNumbers.push(empDiesNumbers[i]) //Push the entry onto the new list
			n = empDiesNumbers[i][0]; //grab the n, d, and mod for the entry
			d = empDiesNumbers[i][1];
			mod = empDiesNumbers[i][2];
			
			//Update the display innerHTML string- using j for index in the new 
			if (empDies == ''){empDies = empDies + "<span id='eD_"+j+"' onclick='remEmpDie();' style='color:blue;'>" + n + 'd' + d + '  +' + mod + "</span>";}
			else{empDies = empDies + "<br/> <span id='eD_"+j+"' onclick='remEmpDie();' style='color:blue;'>" + n + 'd' + d + '  +' + mod + "</span>";}
			j = j + 1; //increment the new index counter to set the ID
		}
	}
	empDiesNumbers = n_empDiesNumbers; //Replace the old list with the new one
	document.getElementById('empDiesList').innerHTML = empDies; //Update the innerHTML
}

//Function to add a die for the empowerment trials
function addDies(){
	//Grab n, d, and mods from inputs
	let n = parseInt(document.getElementById('empNInp').value);
	let d = parseInt(document.getElementById('empDInp').value);
	let mod = parseInt(document.getElementById('empModInp').value);

	//Make a dies list for each die set and push onto the list
	let dies = [n,d,mod];
	empDiesNumbers.push(dies);

	//Build the new div strong
	let empDies = '';
	for (let i=0;i<empDiesNumbers.length;i++){//looping over all entries
		n = empDiesNumbers[i][0]; //Grab each entry's n, d, and mod
		d = empDiesNumbers[i][1];
		mod = empDiesNumbers[i][2];
		
		//Build the inner div string
		if (empDies == ''){empDies = empDies + "<span id='eD_"+i+"' onclick='remEmpDie();' style='color:blue;'>" + n + 'd' + d + '  +' + mod + "</span>";}
		else{empDies = empDies + "<br/> <span id='eD_"+i+"' onclick='remEmpDie();' style='color:blue;'>" + n + 'd' + d + '  +' + mod + "</span>";}
	}

	document.getElementById('empDiesList').innerHTML = empDies;
}

//FUnction to clear all empower trial dies
function clearDies(){
	document.getElementById('empDiesList').innerHTML = ''; //wipe the inner div html
	empDiesNumbers = []; //clear the list of dies
}

function remCond(event){
	//Function to remove a turn based condition on click
	let cid_N = event.target.id; //Grab the caller's target id
	N = getCIndex(cid_N); //Get the card index from that id
	ind = parseInt(cid_N[6]); //Grab the counter's position
	document.getElementById('cndCtr'+ind+'_'+N).innerHTML = ''; //set it to empty
}

function cCond(event){
	//Function to add a turn based condition counter
	let cid_N = event.target.id; //Grab the caller's target ID
	N = getCIndex(cid_N); //Make it an index
	amt = parseInt(document.getElementById('camt_'+N).value); //Grab the amount in the box

	if (isNaN(amt)){alert("No condition duration set");} //If parseInt returned a NaN, the number wasn't set
	else { //otherwise
		let i = 1; //Loop over all the condition counters (there's 6 for aesthetics)
		while (i<7){
			if (document.getElementById('cndCtr'+i+'_'+N).innerHTML == ''){ //if you find an empty one
				document.getElementById('cndCtr'+i+'_'+N).innerHTML = amt; //add in the new counter
				i = 10; //mark as >7 for loop termination
			}
			i = i + 1;//increment while looking
		}
		if (i==7){alert("I set it up for only 6 conditions so it wouldn't be ugly, sorry...")} //If no empty spot, notify and apologize
	}
}

function advanceTurn(){
	//function to advance the turn on click
	if (combatants.length == 0){ //If there's no cards loaded, don't bother
		alert("No combatants");
		return false
	}
	//Otherwise
	currentTurn = (currentTurn + 1)%combatants.length; //increment and loop over number of combatants
	updateCombs = true; //set flag to update the order
	turnAdvanced = true; //set flag to check turn based conditions
}

function loadRoll(event){
	//Function to roll dies on click of atk rolls
	let cid_N = event.target.id; //Grab target id
	atk = document.getElementById(event.target.id).innerHTML; //get the atk value in the trigger HTML
	document.getElementById("dieInput").value = atk; //Load the die roll into the input box
	rollDies(); //Call the standard roll
}

function makeInit(str){
	//function to prep initiative on adding a combatant-
	// when it's '+something', rolls 1d20 and adds the something
	// otherwise, adds with the init as the input value

	let i = 0;//loop index
	let n = 0; //output parsed int
	let rollInit = false; //Flag for if it needs a roll
	while (i < str.length){ //Loop over the whole string
		
		if (str[i] == "+"){rollInit = true;} //If there's a + in there, consider it a modifier
		else{ //Otherwise, try to parse a single char to an int, and convert the sequence to the full int
			c = parseInt(str[i]);
			if (!isNaN(c)) {n = 10*n + c;}
		}
		i = i + 1; //increment the loop
	}
	if (rollInit){ //We you decided it was a modifier, roll 1d20 and add the mod
		return Math.floor(Math.random()*20)+1+n;
	}
	else{
		return n;//otherwise it's already rolled
	}
}

function parseAtks(str){
	//A function to convert an attack string into a sequence of rollable ones
	let atks = []; //The list of rolls
	let i = 0; //loop index
	let s = ''; //staged output string
	while (i<str.length){ //Looping over the input string
		if ((str[i]==';')||(str[i]==',')){ //If spotting a separator
			atks.push(s); //Push the currently built string into output
			s = '';//reset the current string
		}
		else{s = s + str[i];} //otherwise keep building
		i = i + 1;//increment over loop
	}
	if (s != ''){atks.push(s);}//if the last output isn't empty, add it, too
	return atks;//return the list
}

function addCombatant(){
	//A function to build and add a new combatant card to the full list on click

	//Grab the parameters from the input block
	let number = parseInt(document.getElementById("nComb").value); //number of this card to make
	let hp = parseInt(document.getElementById("hpInp").value); //hp
	let ac = parseInt(document.getElementById("acInp").value); //ac
	let init_str = document.getElementById("initInp").value; //initiative
	let atks = document.getElementById("atksInp").value; //atk strings
	let name = document.getElementById("nameInp").value; //name

	//Make up the attacks list
	atks = parseAtks(atks);
	toInitCombs = []; //parameters to update div of card later

	//Looping over the number of cards to make
	for(let j=0;j<number;j++){

		init = makeInit(init_str); //Process the initiative ('+K' vs 'K')

		//Grab an index from the number of combatants so far and increment
		let cN = nCombatants;
		nCombatants = nCombatants + 1;

		//Make a new unattached div
		cmbDiv = document.createElement('div');
		cmbDiv.id = "combatant_"+cN; //give it an index coded ID
		cmbDiv.classList.add("combatant") //give it the combatant class
	
		combT = ""; //Build string for div's inner HTML
		let i = 0;//string loop index
		while (i < cProto.length){ //Iterate over the prototype
			if (cProto[i] == 'Æ'){combT = combT + cN;} //If you find a place where the index goes, add the index
			else{combT = combT + cProto[i];} //otherwise keep building
			i = i + 1; //increment
		}
		cmbDiv.innerHTML = combT //set the div's inner HTML

		combatant = [cmbDiv,init] //Add the div/initiative combo as a list for later sorting

		combatantIn = false; //Flag for if you've sorted the combatant into the list
		combNew = []; //Fresh sorting list
	
		while (combatants.length > 0){ //looping over prior combatants
			cmb = combatants.pop(); //Pull first card
			if ((cmb[1] < combatant[1])||(combatantIn)){ //if it goes ahead of the new one and the new one isn't in there yet
				combNew.push(cmb); //put it in
			}
			else{ //otherwise
				combNew.push(combatant); //put the new one int
				combatantIn = true; //mark that you added the new one
				combNew.push(cmb);//now add the old one
			}
		}
		if (!combatantIn){ //if you did all that and the new card isn't in, it goes at the end
			combNew.push(combatant); //push it on
			combatantIn = true; //I know, it's not necessary but it makes me feel better
		}

		combatants = combNew; //replace the old list with the new sorted one
		combatants.reverse(); //reverse to put them in descending order again

		toInitCombs.push([cN,name,hp,ac,init,atks]); //Put the new card updates in the queue
		updateCombs = true; //mark that there are updates to do
	}
}

function getCIndex(str){
	//A function to get the index number from an element ID
	let i = 0; //incrementor to 0
	while ((i<str.length)&(str[i]!="_")){i=i+1;} //loop until you see the '_'
	sN = ''; //New parse string
	i = i + 1; //increment over the '_'
	while (i<str.length){sN = sN + str[i];i=i+1;}//grab remaining string as N
	return parseInt(sN); //Pares to int and return
}

function cDam(event){
	//Function to appply damage to a card on click
	let cid_N = event.target.id; //Grab target's id
	N = getCIndex(cid_N) //get index from it
	amt = parseInt(document.getElementById('camt_'+N).value); //Grab amount from box
	if (!isNaN(amt)){ //If not none
		hp = parseInt(document.getElementById('cHP_'+N).innerHTML); //grab the current hp from the element 
		hp = hp - amt; //subtract damage
		document.getElementById('cHP_'+N).innerHTML = hp; //update new value
		if (hp < 0){document.getElementById('combatant_'+N).className = 'combatantout';} //if hp<0, mark that the combatant is incapacitated
	}
}

function cHeal(event){
	//Function to heal a combatant card, mirror of above
	let cid_N = event.target.id;
	N = getCIndex(cid_N)
	amt = parseInt(document.getElementById('camt_'+N).value);
	if (!isNaN(amt)){
		hp = parseInt(document.getElementById('cHP_'+N).innerHTML);
		hp = hp + amt; //Add amt instead of subtracting
		document.getElementById('cHP_'+N).innerHTML = hp;
		if (hp > 0){document.getElementById('combatant_'+N).className = 'combatant';} //Correct card incapicitation style
	}
}

function cRem(event){
	//Function to remove a combatant card on click
	let cid_N = event.target.id;// get id
	N = getCIndex(cid_N); // make index
	
	divID = "combatant_"+N; //Make combatant card ID
	combNew = []; //Updated combatants list
	while (combatants.length > 0){ //loop over combatants
		cmb = combatants.pop(); //pop the top
		if (cmb[0].id != divID){combNew.push(cmb);} //if it's the one to remove, remove it
	}
	combatants = combNew; //mreplace old list
	combatants.reverse(); //reverse to descending order again 
	updateCombs = true;//set note to update the card list
}

function sendString(str){
	//Send a string over websocket
	if ((str != '') && (str != sendStringPrev)){sock.send(str);} //if it's not empty or a double-send, send it
	else{pass();} //else, doNothing

}

function rollDies(){
	//Function to call a die roll to python
	let dieString = document.getElementById('dieInput').value; //Get the input roll string
	sendString("die§"+dieString); //format message- we use § to separate the request type from the request itself
	didRoll = true; //FLag that a roll was done for later box updates
}

function makeMagic(){
	//Function to Python to make magic items
	let magicItemsNumber = document.getElementById('magicItemsNumber').value; //Grab how many
	let quirkProbability = document.getElementById('quirkProbability').value; //grab the quirk probability
	let materialChance = document.getElementById('materialChance').value; //grab the atypical material chance

	//Send formatted reques string
	sendString("magicitem§"+magicItemsNumber + "," + quirkProbability + "," + materialChance);
}

function makeChar(){
	//Function to call python for a background
	sendString("background§")
}

function clearHist(){
	//Function to wipe results history
	fullHist = ''; //Set history to ;;
	document.getElementById('outputText').innerHTML = baseResultHTML; //Set results box to the base, only
}

function saveHist(){
	//Function to tell python to save the result history
	sendString("save§"+fullHist);
}

function saveCbt(){
	//Function to save current combat manager status

	//Lists to hold HTMLs, classes, ids, and initiatives of combatant cards
	innerHTMLs = [];
	outerHTMLs = [];
	classes = [];
	ids = [];
	inits = [];

	//Loop over all cards
	for (let i=0;i<combatants.length;i++){
	
		//Grab the inner and outer html of the div
		iHTML = combatants[i][0].innerHTML;
		oHTML = combatants[i][0].outerHTML;

		//Push class, id, html, and initiative date into lists
		classes.push(combatants[i][0].className);
		ids.push(combatants[i][0].id);
		innerHTMLs.push(iHTML);
		outerHTMLs.push(oHTML);
		inits.push(combatants[i][1]);
	}

	//Convert card data and manager variables to JSON strings
	nCombatantsSTFY = JSON.stringify(nCombatants); //number of combatants
	currentTurnSTFY = JSON.stringify(currentTurn); //Current turn
	innerHTMLsSTFY = JSON.stringify(innerHTMLs); //HTMLs
	outerHTMLsSTFY = JSON.stringify(outerHTMLs); //^
	initsSTFY = JSON.stringify(inits); //Iniatives
	classesSTFY = JSON.stringify(classes); //Classes
	idsSTFY = JSON.stringify(ids); //IDs

	//Take all those and put them in localstorage
	localStorage.setItem("nCombatantsSTFY",nCombatantsSTFY);
	localStorage.setItem("currentTurnSTFY",currentTurnSTFY);
	localStorage.setItem("innerHTMLsSTFY",innerHTMLsSTFY);
	localStorage.setItem("outerHTMLsSTFY",outerHTMLsSTFY);
	localStorage.setItem("initsSTFY",initsSTFY);
	localStorage.setItem("classesSTFY",classesSTFY);
	localStorage.setItem("idsSTFY",idsSTFY);
}

function loadCbt(){
	//Function to load combatant cards from local storage

	clearCbt(); //Clear all the prior to not have conflicts

	//Load in numbers, turn, HTMLs, initiatives, classes, and IDs of saved combat manager status
	nCombatantsSTFY = localStorage.getItem("nCombatantsSTFY");
	currentTurnSTFY = localStorage.getItem("currentTurnSTFY");
	innerHTMLsSTFY = localStorage.getItem("innerHTMLsSTFY");
	outerHTMLsSTFY = localStorage.getItem("outerHTMLsSTFY");
	initsSTFY = localStorage.getItem("initsSTFY");
	classesSTFY = localStorage.getItem("classesSTFY");
	idsSTFY = localStorage.getItem("idsSTFY");

	//Convert all the above from JSON strings into either combat manager variables or ones to load into divs
	currentTurn = JSON.parse(currentTurnSTFY);
	nCombatants = JSON.parse(nCombatantsSTFY);
	innerHTMLs = JSON.parse(innerHTMLsSTFY);
	outerHTMLs = JSON.parse(outerHTMLsSTFY);
	inits = JSON.parse(initsSTFY);
	classes = JSON.parse(classesSTFY);
	ids = JSON.parse(idsSTFY);

	//For each HTML segment in the lists
	for(let i=0;i<innerHTMLs.length;i++){

		cmbDiv = document.createElement('div'); //Make a new div
		cmbDiv.id = ids[i]; //Set its ID
		cmbDiv.className = classes[i]; //Set its class
		cmbDiv.outerHTML = outerHTMLs[i]; //load in HTMLs
		cmbDiv.innerHTML = innerHTMLs[i]; //^
		combatants.push([cmbDiv,inits[i]]); //Push it onto the combatants list w/ its initiative
	}
	updateCombs = true; //Set update flag
}

function clearCbt(){
	//Function to clear the combat manager on click
	for (let i=0;i<combatants.length;i++){ //Loop over all combatant cards
		cbt = combatants[i][0]; //grab the associated div
		cbt.remove(); //Remove that div from the dom
	}
	combatants = []; //Set combatants list empty
	nCombatants = 0; //clear the number of combatants to 0
	currentTurn = 0; //Reset to turn 0
	updateCombs = true; //Mark to run and update
}

function onReply(event){
	//Reply handler for websockets communication
	WSmessage=event.data; //Grab the message itself
	fullHist = WSmessage + "<hr>" + fullHist; //Update the history, separate with an <hr> for pretty

	document.getElementById('outputText').innerHTML = baseResultHTML+fullHist; //Set the results column to the base header plus the full history
	document.getElementById('splashImage').src = ''; //remove the splash image

	//If a roll was called for this reply	
	if (didRoll){
		let i = 0; //Iterate over all combatant card indices 
		while (i<=nCombatants-1){//(<=nC-1 because it clarifies it in my mind)
			amtElem = "camt_"+i; //Grab the amount box for each card
			document.getElementById(amtElem).value = parseInt(document.getElementById('rollRes').innerHTML); //Add the roll result to that box
			i = i + 1; //increment
		}
		didRoll = false; //clear roll flag
	}
}

