import bpy


import bpy
import math
import numpy as np
import itertools

def get_grease_pencil(gpencil_obj_name='GPencil') -> bpy.types.GreasePencil:
    """
    Return the grease-pencil object with the given name. Initialize one if not already present.
    :param gpencil_obj_name: name/key of the grease pencil object in the scene
    """

    # If not present already, create grease pencil object
    if gpencil_obj_name not in bpy.context.scene.objects:
        bpy.ops.object.gpencil_add(location=(0, 0, 0), type='EMPTY')
        # rename grease pencil
        bpy.context.scene.objects[-1].name = gpencil_obj_name

    # Get grease pencil object
    gpencil = bpy.context.scene.objects[gpencil_obj_name]

    return gpencil


def get_grease_pencil_layer(gpencil: bpy.types.GreasePencil, gpencil_layer_name='GP_Layer',
                            clear_layer=False) -> bpy.types.GPencilLayer:
    """
    Return the grease-pencil layer with the given name. Create one if not already present.
    :param gpencil: grease-pencil object for the layer data
    :param gpencil_layer_name: name/key of the grease pencil layer
    :param clear_layer: whether to clear all previous layer data
    """

    # Get grease pencil layer or create one if none exists
    if gpencil.data.layers and gpencil_layer_name in gpencil.data.layers:
        gpencil_layer = gpencil.data.layers[gpencil_layer_name]
    else:
        gpencil_layer = gpencil.data.layers.new(gpencil_layer_name, set_active=True)

    if clear_layer:
        gpencil_layer.clear()  # clear all previous layer data

    # bpy.ops.gpencil.paintmode_toggle()  # need to trigger otherwise there is no frame

    return gpencil_layer


# Util for default behavior merging previous two methods
def init_grease_pencil(gpencil_obj_name='GPencil', gpencil_layer_name='GP_Layer',
                       clear_layer=True) -> bpy.types.GPencilLayer:
    gpencil = get_grease_pencil(gpencil_obj_name)
    gpencil_layer = get_grease_pencil_layer(gpencil, gpencil_layer_name, clear_layer=clear_layer)
    return gpencil_layer

def draw_line(gp_frame, p0: tuple, p1: tuple,thickness=10):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    
    gp_stroke.line_width = thickness

    # Define stroke geometry
    gp_stroke.points.add(count=2)
    gp_stroke.points[0].co = p0
    gp_stroke.points[1].co = p1
    return gp_stroke

def draw_circle(gp_frame, center: tuple, radius: float, segments: int):
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    gp_stroke.draw_cyclic = True        # closes the stroke
    
    #gp_stroke.line_width = 100
    #gp_stroke.material_index = 1

    # Define stroke geometry
    angle = 2*math.pi/segments  # angle in radians
    gp_stroke.points.add(count=segments)
    for i in range(segments):
        x = center[0] + radius*math.cos(angle*i)
        y = center[1] + radius*math.sin(angle*i)
        z = center[2]
        gp_stroke.points[i].co = (x, y, z)

    return gp_stroke

def rotate_stroke(stroke, angle, axis='z'):
    # Define rotation matrix based on axis
    if axis.lower() == 'x':
        transform_matrix = np.array([[1, 0, 0],
                                     [0, math.cos(angle), -math.sin(angle)],
                                     [0, math.sin(angle), math.cos(angle)]])
    elif axis.lower() == 'y':
        transform_matrix = np.array([[math.cos(angle), 0, -math.sin(angle)],
                                     [0, 1, 0],
                                     [math.sin(angle), 0, math.cos(angle)]])
    # default on z
    else:
        transform_matrix = np.array([[cos(angle), -math.sin(angle), 0],
                                     [sin(angle), math.cos(angle), 0],
                                     [0, 0, 1]])

    # Apply rotation matrix to each point
    for i, p in enumerate(stroke.points):
        p.co = transform_matrix @ np.array(p.co).reshape(3, 1)

def draw_sphere(gp_frame, center: tuple, radius: int, circles: int):
    angle = math.pi / circles
    for i in range(circles):
        circle = draw_circle(gp_frame, center, radius, 32)
        rotate_stroke(circle, angle*i, 'x')
        print(angle * i)


# 四次元点を３次元座標に透視投影(いいかげん。u=1のときにx,y,zがscale倍される)
def project(point4d,scale=0.75):
    x,y,z,u=point4d
    s= (scale-1)*(u-1)+scale
    return [x*s,y*s,z*s]

#p0,p1のユークリッド距離
def distance(p0,p1):
    d=0
    for a,b in zip(p0,p1):
        d+=(a-b)**2
    return np.sqrt(d)

#点群pointsから距離２（最短距離）の点ペアを列挙
def get_pairs(points, target_distance=2.1):
    pairs=[]
    for p in itertools.combinations(points,2):
        d=distance(p[0],p[1])
        if(d<target_distance):
            pairs.append( [p[0],p[1]]) 
    return pairs


#頂点ペアを3Dプロット
def plot_lines(frame,pairs):
    for p in pairs:
        p[0]=project(p[0])
        p[1]=project(p[1])
        print(p[0])
#        draw_line(frame, p[0], p[1]):


# xu,yu,zu平面での回転
# https://mixedmoss.com/4dimensionGeometry/8-cells/developement%20of%20super%20cube.pdf
def rotate(point, plane, theta_degree):
    t=[]
    X=[1,0,0,0]
    Y=[0,1,0,0]
    Z=[0,0,1,0]
    U=[0,0,0,1]
    if(plane=="xy"):
        t=[X,Y,Z,U]
    elif(plane=="yz"):
        t=[Y,Z,X,U]
    elif(plane=="xz"):
        t=[X,Z,Y,U]
    elif(plane=="xu"):
        t=[X,U,Y,Z]
    elif(plane=="yu"):
        t=[Y,U,X,Z]
    elif(plane=="zu"):
        t=[Z,U,X,Y]
    else:
        print("unknown plane:"+plane)
        exit(-1)
    t=np.matrix(t)

    theta = theta_degree/180*np.pi
    mat=np.matrix([
        [np.cos(theta), -np.sin(theta),0,0 ],
        [np.sin(theta), np.cos(theta),0,0 ],
        [0,0,1,0],
        [0,0,0,1]        
    ])
    point=np.matrix(point).reshape(4,1)
    rotated_point=t.T*mat*t*point
    rotated_point =rotated_point.reshape(1,4).tolist()[0]
    return rotated_point

# 超立方体を作成し、指定したplaneでangle[deg]回転させる
# planesは文字列のリストで、平面はxyzuのうち２文字を指定
# 複数指定すると同じ角度で複数平面回転を行う。
# planes=["xy"]       xy平面でangle回転
# planes=["xu","yu"]  xu平面、yu平面でangleずつ回転
def plot_tesseract(frame,planes, angle):
    # 超立方体の頂点を作成しつつ回転させる
    dimensions=4
    points=[]
    for x in itertools.product([1,-1],repeat=dimensions):
        p=x
        for plane in planes:
            p=rotate(p,plane,angle)
        points.append(p)

    # 距離が２（最も近い距離）の頂点ペアを列挙する
    pairs=get_pairs(points)

    # 描画
    plot_lines(frame,pairs)

    
    
if __name__ == "__main__":
    gp_layer = init_grease_pencil()
    
    angle_step=1 #1フレームあたりの角度ステップ
#    frames=int(180/angle_step)
    frames=1
    for frame in range(0,frames):
        angle=i*angle_step
        gp_frame = gp_layer.frames.new(frame)

        plot_tesseract(gp_frame,["xu"],angle)    
    