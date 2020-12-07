var __occurrence__sequence = 0;

class dolfin_occurrence_cluster {
    constructor() {
        this.occurrence_hash = {};
    }
    add_occurrence(a_occ){

    }
}

class dolfin_occurrence {
    constructor(id,latitude, longitude) {
        this.id = id;
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
        this.parent = null;
        this.children = [];
        this.cluster_max_show = 5;
    }
    add_children(a_occ){
        this.children[this.children.length] = a_occ;
        //console.log( "add children:", this.id, a_occ.id, " children count:", this.children.length);
    }
    calculate_distance(a_occ){
        dist = this.distance(this.latitude, this.longitude, a_occ.latitude, a_occ.longitude);
        return dist;
    }
    get_marker(){
        return this.marker_instance;
    }
    set_map(map){
        this.marker_instance.setMap(map);
    }
    add_occurrence(fin_id, occ_date, occ_datetime){
        if(!this.finid_list.includes(fin_id)){
            this.finid_list[this.finid_list.length] = fin_id;
            this.occurrence_data[fin_id] = {};
        }
        var occ_datetime_hash = this.occurrence_data[fin_id];
        if( !Object.keys(occ_datetime_hash).includes(occ_date) ){
            occ_datetime_hash[occ_date] = [];
            
        }
        occ_datetime_hash[occ_date][occ_datetime_hash[occ_date].length] = occ_datetime;
    }
    set_visible( visible_true ){
        if( visible_true ) {
            this.set_map(map);
        } else {
            this.set_map(null);
        }
        this.visible = visible_true;
    }
    set_visibility(finid_list,date_list){
        //console.log(this);
        this.reset_display();
        this.visible = false;
        for(var fidx=0;fidx<finid_list.length;fidx++){
            if(this.finid_list.includes(finid_list[fidx])) {
                var occ_date_hash = this.occurrence_data[finid_list[fidx]];
                for(var didx=0;didx<date_list.length;didx++){
                    if(Object.keys(occ_date_hash).includes(date_list[didx])) {
                        this.visible = true;
                        var prev_dt = '';
                        var dt_count = 0;
                        for(var dtidx=0;dtidx<occ_date_hash[date_list[didx]].length;dtidx++){
                            var dt = occ_date_hash[date_list[didx]][dtidx];
                            //console.log(occ_date_hash[date_list[didx]])
                            if( dt != prev_dt && prev_dt != '') {
                                this.add_display(finid_list[fidx],prev_dt, dt_count);
                                dt_count = 0;
                            }
                            dt_count += 1;
                            prev_dt = dt;
                        }
                        this.add_display(finid_list[fidx], prev_dt, dt_count);
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
        this.div_content.style.width = '200px';
        this.div_content.style.height = '20px';
        this.div_content.style.padding = '3px';
        this.display_row = 0;
        this.div_content.appendChild(document.createTextNode('#'+String(this.id)));
        this.div_content.appendChild(document.createElement('br'));
        this.infowindow_instance.setContent(this.div_content);
        //console.log(this.id,"children:", this.children.length);
    }
    add_display(a_finid, a_datetime, a_datetime_count){
        this.div_content.appendChild(document.createTextNode(a_finid + " " + a_datetime + "(" + String(a_datetime_count) + ")"));
        this.div_content.appendChild(document.createElement('br'));
        this.display_row += 1;
        this.div_content.style.height = String( 17 * (this.display_row + 1 )) + 'px';
    }
    update_cluster_display(){
        //console.log("update display", this.id, this.div_content)
        var local_div = document.createElement("div");
        //console.log("update display 1", this.id, this.children.length, local_div);
        local_div.appendChild(this.div_content);
        //console.log("update display 2", this.id, this.children.length, local_div);
        var max_len = this.children.length;
        if( max_len > this.cluster_max_show ) { max_len = this.cluster_max_show;}
        //div.appendChild(document.createTextNode("children"))
        for(idx=0;idx<max_len;idx++){
            local_div.appendChild(this.children[idx].div_content)
        }
        //console.log(div)
        if( this.children.length > this.cluster_max_show ) { 
            //console.log(this.id, "children length > 3");
            local_div.appendChild(document.createElement("div").appendChild(document.createTextNode("...(+" + String( this.children.length-max_len)+")"))); 
        }
        //console.log("update display 3", this.id, this.children.length, this.div_content, local_div);
        this.infowindow_instance.setContent(local_div);
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
        this.div_content = div_element;
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