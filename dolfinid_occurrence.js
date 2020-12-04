var __occurrence__sequence = 0;

class dolfin_occurrence_cluster {
    constructor() {

    }
}

class dolfin_occurrence {
    constructor(latitude, longitude) {
        this.location_key = latitude + '_' + longitude;
        this.latitude = latitude;
        this.longitude = longitude;
        this.occurrence_data = {};
        this.finid_list = [];
        this.display_hash = {};
        this.display_row = 0;
        this.visible = true;
        this.position  = new kakao.maps.LatLng(this.latitude, this.longitude);
        this.marker_instance = new kakao.maps.Marker({position: this.position});
        this.div_instance = '<div class="label" style="padding:5px;" id="' + this.location_key + '"></div>';
        this.overlay_instance = new kakao.maps.CustomOverlay({'position': this.position,'marker': this.marker_instance,'content': this.div_instance});
        //this.break_point_label = '';
        this.iw_content = '<div style="padding:5px;"></div>';
        this.iw_position = this.position;
        this.infowindow_instance = new kakao.maps.InfoWindow({'position' : this.position, 'content' : this.div_instance, 'removable' : true});
    }
    calculate_distance(a_occ){
        lat_difference = this.latitude - a_occ.latitude;
        lon_difference = this.longitude - a_occ.longitude;
    }
    get_marker(){
        return this.marker_instance;
    }
    set_map(map){
        this.marker_instance.setMap(map);
    }
    add_occurrence(fin_id, occ_date){
        if(!this.finid_list.includes(fin_id)){
            this.finid_list[this.finid_list.length] = fin_id;
            this.occurrence_data[fin_id] = []
        }
        if( !this.occurrence_data[fin_id].includes(occ_date) ){
            var date_list = this.occurrence_data[fin_id];
            date_list[date_list.length] = occ_date;
        }
    }
    set_visibility(finid_list,date_list){
        //console.log(this);
        this.reset_display();
        this.visible = false;
        for(var fidx=0;fidx<finid_list.length;fidx++){
            if(this.finid_list.includes(finid_list[fidx])) {
                var occ_date_list = this.occurrence_data[finid_list[fidx]];
                for(var didx=0;didx<date_list.length;didx++){
                    if(occ_date_list.includes(date_list[didx])) {
                        this.visible = true;
                        this.add_display(finid_list[fidx],date_list[didx]);
                    }
                }
            }
        }
        this.infowindow_instance.setContent(this.div_content);
    }
    reset_display(){
        this.display_hash = {};
        this.div_content = document.createElement('div');
        this.div_content.style.fontSize = '12px';
        this.div_content.style.width = '150px';
        this.div_content.style.height = '20px';
        this.div_content.style.padding = '3px';
        this.display_row = 0;
    }
    add_display(a_finid, a_date){
        if( this.display_row > 0 ){this.div_content.appendChild(document.createElement('br'));}
        this.div_content.appendChild(document.createTextNode(a_finid + " " + a_date));
        this.display_row += 1;
        this.div_content.style.height = String( 15 * this.display_row ) + 'px';
    }
    set_display(a_finid, a_date){
        //return
        //display_hash = this.display_hash;
        //console.log(this, this.display_hash);
        key_list = Object.keys(this.display_hash);
        //console.log(key_list);
        if(!(key_list.includes(a_finid))){
            this.display_hash[a_finid] = [];
        }
        if(!(this.display_hash[a_finid].includes(a_date))){
            this.display_hash[a_finid][this.display_hash[a_finid].length] = a_date;
            this.display_hash[a_finid].sort();
        }
	    var div_element = document.createElement('div');
        var finid_list = Object.keys(this.display_hash);
        var div_text_list = [];
        finid_list.sort();
        for(idx=0;idx<finid_list.length;idx++){
            var date_list = this.display_hash[finid_list[idx]];
            var date_text = date_list.join(", ");
            var tn = document.createTextNode(finid_list[idx] + "(" + date_text + ")<br/>");
            div_element.appendChild(tn);
        }
        this.infowindow_instance.setContent(div_element);
    }
    distance(lat1, lon1, lat2, lon2 ) {
        if ((lat1 == lat2) && (lon1 == lon2)) {
            return 0;
        }
        else {
            var radlat1 = Math.PI * lat1/180;
            var radlat2 = Math.PI * lat2/180;
            var theta = lon1-lon2;
            var radtheta = Math.PI * theta/180;
            var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
            if (dist > 1) {
                dist = 1;
            }
            dist = Math.acos(dist);
            dist = dist * 180/Math.PI;
            dist = dist * 60 * 1.1515;
            dist = dist * 1.609344;
            return dist;
        }
    }
}