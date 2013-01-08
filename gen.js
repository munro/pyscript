/*jslint node: true, vars: true */

'use strict';

function createGenerator(fn) {
    return function () {
        //var pieces = fn.apply(this, arguments);
        var pieces = [];
        var gen = [];
        Object.defineProperty(gen, 'send', {
            enumerable: false,
            value: function (a) {
                return pieces.shift()(a);
            }
        });
        gen.length = {
            valueOf: function () {
                var index = 0;
                while (true) {
                    console.log('rwarr', gen[index]);
                    try {
                        gen[index] = gen.send();
                        index += 1;
                    } catch (e) {
                        console.log('nope', e);
                        return index;
                    }
                }
            }
        };
        return gen;
    };
}

var blah = createGenerator(function (a) {
    return [function () {
        console.log('hey', a);
        return 123;
    }, function (h) {
        console.log('hey', h);
        throw new Error('StopIteration');
    }];
});

blah(44);

/*var g = blah(44);
console.log('next', g.send());
try {
    console.log('next', g.send('hey'));
} catch (e) {
}*/

//console.log(blah(51).map(function (v) { return 'hey ' + v + ','; }));
