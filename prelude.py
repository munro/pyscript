prelude = '''
/* prelude start */
function map(fn, list) {
    return list.map(fn);
}
function isinstance(obj, t) {
    return obj instanceof t;
}
String.prototype.format = function () {
    throw new Error('todo');
};
String.prototype.__add__ = function (b) {
    if (typeof b !== 'string') {
        throw new Error('TypeError: cannot concatenate \\'str\\' and \\'int\\' objects');
    }
    return this + b;
};
Number.prototype.__sub__ = function (b) {
    return this - b;
};
Number.prototype.__add__ =
Boolean.prototype.__add__ = function (b) {
    return this + b;
};
Array.prototype.__add__ = function (b) {
    return this.concat(b);
};
var modules = {};
function require(module) {
    if (!modules[module]) {
        return window[module];
    }
    if (modules[module][0] === false) {
        modules[module][0] = true;
        modules[module][1] = modules[module][1](require);
    }
}
require.define = function (module, fn) {
    modules[module] = [false, fn];
};
require.init = function (f) {
    require(f);
};
/* prelude end */
'''
