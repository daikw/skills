// QCAD headless drawing library
// Verified on QCAD 3.32.9 Community (macOS)
// Units: coordinates in mm (absolute model space), angles in degrees

var Drawing = function() {
    this.storage = new RMemoryStorage();
    this.spatialIndex = new RSpatialIndexSimple();
    this.doc = new RDocument(this.storage, this.spatialIndex);
    this.di = new RDocumentInterface(this.doc);
    this.op = null;
    this._begin();
};

Drawing.prototype._begin = function() {
    this.op = new RAddObjectsOperation();
};

Drawing.prototype._add = function(entity) {
    this.op.addObject(entity, false);
    return this;
};

Drawing.prototype._flush = function() {
    if (this.op !== null) {
        this.di.applyOperation(this.op);
        this.op = null;
    }
};

// --- Layers ---

Drawing.prototype.addLayer = function(name, color, lineweight) {
    if (this.doc.getLayerId(name) !== -1) return this;
    this._flush();
    var linetypeId = this.doc.getLinetypeId("CONTINUOUS");
    var lw = lineweight || RLineweight.WeightByLayer;
    var layerOp = new RModifyObjectsOperation();
    layerOp.addObject(new RLayer(this.doc, name, false, false,
        new RColor(color || "white"), linetypeId, lw));
    this.di.applyOperation(layerOp);
    this._begin();
    return this;
};

// --- Primitives ---

Drawing.prototype.line = function(x1, y1, x2, y2, layer) {
    var e = new RLineEntity(this.doc,
        new RLineData(new RVector(x1, y1), new RVector(x2, y2)));
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

Drawing.prototype.circle = function(cx, cy, r, layer) {
    var e = new RCircleEntity(this.doc,
        new RCircleData(new RVector(cx, cy), r));
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

Drawing.prototype.arc = function(cx, cy, r, startAngleDeg, endAngleDeg, layer) {
    var startRad = startAngleDeg * Math.PI / 180;
    var endRad = endAngleDeg * Math.PI / 180;
    var e = new RArcEntity(this.doc,
        new RArcData(new RVector(cx, cy), r, startRad, endRad, false));
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

Drawing.prototype.point = function(x, y, layer) {
    var e = new RPointEntity(this.doc,
        new RPointData(new RVector(x, y)));
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

// vertices: [[x,y], [x,y], ...], closed: boolean
Drawing.prototype.polyline = function(vertices, closed, layer) {
    var pl = new RPolylineData();
    for (var i = 0; i < vertices.length; i++) {
        pl.appendVertex(new RVector(vertices[i][0], vertices[i][1]));
    }
    if (closed) pl.setClosed(true);
    var e = new RPolylineEntity(this.doc, pl);
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

// rect: convenience for closed polyline
Drawing.prototype.rect = function(x, y, w, h, layer) {
    return this.polyline([
        [x, y], [x + w, y], [x + w, y + h], [x, y + h]
    ], true, layer);
};

Drawing.prototype.ellipse = function(cx, cy, majorX, majorY, ratio, layer) {
    var e = new REllipseEntity(this.doc,
        new REllipseData(
            new RVector(cx, cy),
            new RVector(majorX, majorY),
            ratio, 0, Math.PI * 2, false));
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

Drawing.prototype.text = function(str, x, y, height, layer) {
    var td = new RTextData();
    td.setText(str);
    td.setAlignmentPoint(new RVector(x, y));
    td.setTextHeight(height || 5);
    var e = new RTextEntity(this.doc, td);
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

// controlPoints: [[x,y], ...], degree: 3 by default
Drawing.prototype.spline = function(controlPoints, degree, layer) {
    var sd = new RSplineData();
    sd.setDegree(degree || 3);
    for (var i = 0; i < controlPoints.length; i++) {
        sd.appendControlPoint(new RVector(controlPoints[i][0], controlPoints[i][1]));
    }
    var e = new RSplineEntity(this.doc, sd);
    if (layer) e.setLayerId(this.doc.getLayerId(layer));
    return this._add(e);
};

// --- Export ---

Drawing.prototype.save = function(path) {
    this._flush();
    var absPath = path;
    if (!new QFileInfo(path).isAbsolute()) {
        absPath = RSettings.getLaunchPath() + "/" + path;
    }
    var result = this.di.exportFile(absPath, "R24 (2010) DXF");
    if (!result) {
        print("QCAD_ERROR: exportFile failed for " + absPath);
    }
    return result;
};

// --- State queries (READ_ONLY) ---

Drawing.prototype.entityCount = function() {
    this._flush();
    this._begin();
    return this.doc.queryAllEntities().length;
};

Drawing.prototype.layerNames = function() {
    return this.doc.getLayerNames();
};

Drawing.prototype.summary = function() {
    this._flush();
    this._begin();
    var ids = this.doc.queryAllEntities();
    var counts = {};
    for (var i = 0; i < ids.length; i++) {
        var e = this.doc.queryEntity(ids[i]);
        var t = e.getType ? e.getType() : "unknown";
        counts[t] = (counts[t] || 0) + 1;
    }
    return {
        entities: ids.length,
        layers: this.doc.getLayerNames(),
        byType: counts
    };
};

// --- Structured result output ---

Drawing.prototype.saveAndReport = function(path) {
    var ok = this.save(path);
    var s = this.summary();
    var result = {
        success: ok,
        output: path,
        entities: s.entities,
        layers: s.layers
    };
    print("QCAD_RESULT:" + JSON.stringify(result));
    return ok;
};
