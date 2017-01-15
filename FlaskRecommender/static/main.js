(function () {
  'use strict';

  angular.module('DiveSiteApp', ['multipleSelect']);

  angular.module('DiveSiteApp').controller('DiveSiteController', function($scope) {
        $scope.suggest = "None"

        $scope.onSubmit = function(e) {
            var siteList = $scope.selectedList


            //remove any suggested sites
            var table = document.getElementById('SuggestedSitesTable')
            if (table.rows.length > 0) {
            var rows = table.getElementsByTagName('tr')
            var i, j, cells, customerId, site,delete_rowId ;

            var rowCount = table.rows.length;
            for (i = rowCount; i > 0; --i) {
                console.log(i)
                //cells = rows[i].getElementsByTagName('td');
                //if (!cells.length) {
                //    continue;
                //}

                //site = cells[2].innerHTML;
                //console.log(site);
                //if (site === item.site) {
                //delete_rowId = i
                document.getElementById('SuggestedSitesTable').deleteRow(i-1);
                //}
            }
        }
            // stop the regular form submission
            //e.preventDefault();

            // collect the form data while iterating over the inputs
            var data = {};
            for (var i = 0, ii = siteList.length; i < ii; ++i) {
                var inputlist = siteList[i];
                data[i] = inputlist;

            }

            // construct an HTTP request
            var xhr = new XMLHttpRequest();
            xhr.open("POST", 'http://0.0.0.0:5000/getSimiliarSite', true);
            xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

            //console.log( data);

            // send the collected data as JSON
            xhr.send(JSON.stringify(data));

            xhr.onloadend = function () {
                if (xhr.readyState === xhr.DONE) {
                    if (xhr.status === 200) {
                        //console.log(xhr.response);
                        //console.log(xhr.responseText);
                        var sitelist2 = xhr.responseText;
                        var json_site_data = JSON.parse(sitelist2);

                        for (var i = 1, ii = json_site_data.length; i < ii; ++i) {
                            var x=document.getElementById('SuggestedSitesTable');
                            //var new_row = x.rows[1].cloneNode(true);
                            var len = x.rows.length;
                            var new_row = x.insertRow(len);
                            new_row.id = "SuggestedRow"

                            var new_cell0 = new_row.insertCell(0)
                            // Append a text node to the cell
                            var newText0  = document.createTextNode(len+1)
                            new_cell0.appendChild(newText0)
                            //new_row.cells[0].innerHTML = len;

                            var new_cell1 = new_row.insertCell(1)
                            var newSpan1 = document.createElement('span')
                            newSpan1.style.fontSize = '25px'

                            var newText1  = document.createTextNode(json_site_data[i].regionAndName)
                            newSpan1.appendChild(newText1)
                            new_cell1.appendChild(newSpan1)
                            var newTD1 = document.createElement('td')
                            var newSpan12 = document.createElement('span')
                            var newText12 = document.createTextNode(json_site_data[i].description)
                            newSpan12.appendChild(newText12)
                            newTD1.appendChild(newSpan12)
                            new_cell1.appendChild(newTD1)


                        }


                    }
                }
            };


        };


   $scope.afterSelectItem = function(item){
    // perform operation on this item after selecting it.



        var x=document.getElementById('SelectedSitesTable');
        //var new_row = x.rows[1].cloneNode(true);
        var len = x.rows.length;
        var new_row = x.insertRow(len);

        var new_cell0 = new_row.insertCell(0)
        // Append a text node to the cell
        var newText0  = document.createTextNode(len)
        new_cell0.appendChild(newText0)
        //new_row.cells[0].innerHTML = len;

        var new_cell1 = new_row.insertCell(1)
        var newSpan1 = document.createElement('span')
        newSpan1.style.fontSize = '25px'

        var newText1  = document.createTextNode(item.regionAndName)
        newSpan1.appendChild(newText1)
        new_cell1.appendChild(newSpan1)
        var newTD1 = document.createElement('td')
        var newSpan12 = document.createElement('span')
        var newText12 = document.createTextNode(item.description)
        newSpan12.appendChild(newText12)
        newTD1.appendChild(newSpan12)

        var newTD2 = document.createElement('td')
        newTD2.style.overflow = 'hidden'




        //load images
        var folder_name = item.region.toLowerCase() + item.name.toLowerCase();
        var folder = "images/" + folder_name;
        //var folder = "/images"
        $.ajax({
            url : "get" + folder,
            success: function (data) {
                var image_list = JSON.parse(data);
                console.log(image_list)
                for(var i = 0, size = image_list.length; i < size ; i++){
                    var pic = image_list[i];
                    var div = document.createElement('div')

                    div.style.float = 'left'
                    div.style.width = '25%'
                    div.style.height = '25%'
                    div.style.padding = '30px'
                    var img = document.createElement('img');
                    img.src = folder + "/" + pic;
                    img.style.height = '35%'
                    img.style.width = 'auto'
                    div.appendChild(img)
                    newTD2.appendChild(div);
                }

                //$(data).find("a").attr("href", function (i, val) {
                //    if( val.match(/\.(jpe?g|png|gif)$/) ) {
                //        $("body").append( "<img src='"+ folder + val +"'>" );
                //    }
                //    });
            }
        });

        newTD1.appendChild(newTD2)
        new_cell1.appendChild(newTD1)


        var siteList = $scope.selectedList

        // collect the form data while iterating over the inputs
        var data = {};
        for (var i = 0, ii = siteList.length; i < ii; ++i) {
            var inputlist = siteList[i];
            data[i] = inputlist;

        }

        // construct an HTTP request
        var xhr = new XMLHttpRequest();
        xhr.open("POST", 'http://0.0.0.0:5000/getSimiliarAdj', true);
        xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

        //console.log( data);

        // send the collected data as JSON
        xhr.send(JSON.stringify(data));

        xhr.onloadend = function () {
            if (xhr.readyState === xhr.DONE) {
                if (xhr.status === 200) {
                console.log(xhr.responseText)
                $scope.similarAdjectives = xhr.responseText;

                }
            }
        }
    }

    $scope.afterRemoveItem = function(item){
    // perform operation on this item after removing it.


    // var i= row.parentNode.parentNode.rowIndex; -->
    //<!-- document.getElementById('POITable').deleteRow(i); -->

    var table = document.getElementById('SelectedSitesTable'),
    rows = table.getElementsByTagName('tr'),
    i, j, cells, customerId, site,delete_rowId ;

    for (i = 0, j = rows.length; i < j; ++i) {
        cells = rows[i].getElementsByTagName('td');
        if (!cells.length) {
            continue;
        }
        site = cells[2].innerHTML;
        console.log(site);
        if (site === item.site) {
            delete_rowId = i
            document.getElementById('SelectedSitesTable').deleteRow(delete_rowId);
        }



}


    }

 });




}());
