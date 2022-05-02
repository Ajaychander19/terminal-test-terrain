class Node:
  #  {"id": id_count, "lat": min_lat, "lng": min_lng, "dlat": max_lat - min_lat, "dlng": 0, "zone": [], "points": []}
    def __init__(self,min_lat,min_lng,dlat,dlng,list):

        self.north_W = None
        self.north_E = None
        self.south_W = None
        self.south_E = None
        self.min_lat = min_lat
        self.min_lng= min_lng
        self.dlat= dlat
        self.dlng = dlng
        self.list=list

    def insert(self):
        # Compare the new value with the parent node
        if self.dlat> 0.5:
           if self.dlng > 3:
                self.north_W = Node(self.min_lat + self.dlat/2.0 ,self.min_lng,self.dlat/2.0,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat + self.dlat/2.0 ,self.min_lng,self.dlat/2.0,self.dlng/2.0,
                                                    self.list))
                self.north_E = Node(self.min_lat + self.dlat/2.0,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat + self.dlat/2.0,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,
                                                    self.dlng/2.0,self.list))
                self.south_W = Node(self.min_lat,self.min_lng,self.dlat/2.0,self.dlng/2.0,self.findArrayOfNode(self.min_lat,
                                                                self.min_lng,self.dlat/2.0,self.dlng/2.0,self.list))
                self.south_E = Node(self.min_lat,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat,self.min_lng + self.dlng/2.0,self.dlat/2.0 ,self.dlng/2.0,self.list))
           else:
               self.north_W = Node(self.min_lat + self.dlat/2.0, self.min_lng, self.dlat / 2.0, self.dlng,
                                   self.findArrayOfNode(self.min_lat + self.dlat/2.0, self.min_lng, self.dlat / 2.0,
                                                   self.dlng, self.list))
               self.south_W = Node(self.min_lat, self.min_lng, self.dlat/2.0, self.dlng,
                                   self.findArrayOfNode(self.min_lat, self.min_lng, self.dlat/2.0, self.dlng,self.list))
        else:
           if self.dlng > 0.25:
                self.north_W = Node(self.min_lat ,self.min_lng,self.dlat,self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat ,self.min_lng,self.dlat,self.dlng/2.0, self.list))
                self.north_E = Node(self.min_lat ,self.min_lng + self.dlng/2.0, self.dlat, self.dlng/2.0,
                                    self.findArrayOfNode(self.min_lat ,self.min_lng + self.dlng/2.0, self.dlat, self.dlng/2.0, self.list))
           else:
               self.north_W = None
               self.north_E = None
               self.south_W = None
               self.south_E = None
        if self.north_W is not None:
            self.north_W.insert()
        if self.north_E is not None:
            self.north_E.insert()
        if self.south_W is not None:
            self.south_W.insert()
        if self.south_E is not None:
            self.south_E.insert()
    def findArrayOfNode(self,min_lat,min_lng,dlat,dlng, listItem):
        list=[]
        if len(listItem)!=0:
            for item in listItem:
                if (item["Latitude"] - min_lat <= dlat)&(item["Longitude"]- min_lng<=dlng):
                    list.append(item)
        return list

    def PrintTree(self):
        if self.north_W:
            self.north_W.PrintTree()
        if self.north_E:
            self.north_E.PrintTree()
        if self.south_W:
            self.south_W.PrintTree()
        if self.south_E:
            self.south_E.PrintTree()
        # if ((self.north_W == None) & (self.north_E == None) &(self.south_W == None)&(self.south_E == None)):
       # print({(self.min_lat, self.min_lng, self.dlat, self.dlng)})


    def PreorderTraversal(self,root):
        res=[]
        if root:
           # if bool(root.min_lat)==False:
            a= {"lat": str(root.min_lat), "lng": str(root.min_lng), "dlat": str(root.dlat),"arrayPoint": root.list,"dlng": str(root.dlng), "zone":
                [self.PreorderTraversal(root.north_W),
                 self.PreorderTraversal(root.north_E),
                 self.PreorderTraversal(root.south_W),
                 self.PreorderTraversal(root.south_E)]}

            a["zone"] = [i for i in a["zone"] if i]
            res.append(a)
        return res



# root = Node(0,0,2,1,[])
# root.insert()
# #print(root.PreorderTraversal(root))
# print(root.PreorderTraversal(root)[0])


